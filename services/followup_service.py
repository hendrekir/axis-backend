"""
Follow-up tracker — detects emails sent 3+ days ago with no reply.

Scans sent_emails_cache, cross-references with received emails by
subject/recipient to find unanswered threads. Creates follow_up records
and surfaces them as urgency 6 items in dispatch.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import FollowUp, SentEmailsCache, ThreadMessage, User

logger = logging.getLogger("axis.followup")


async def scan_for_missing_replies(user: User, db: AsyncSession) -> list[dict]:
    """Find sent emails older than 3 days with no reply. Returns new follow-up items."""
    cutoff = datetime.utcnow() - timedelta(days=3)

    # Get sent emails older than 3 days
    result = await db.execute(
        select(SentEmailsCache)
        .where(
            SentEmailsCache.user_id == user.id,
            SentEmailsCache.sent_at <= cutoff,
            SentEmailsCache.sent_at >= datetime.utcnow() - timedelta(days=14),  # Only look back 2 weeks
        )
        .order_by(SentEmailsCache.sent_at.desc())
        .limit(30)
    )
    sent_emails = result.scalars().all()

    if not sent_emails:
        return []

    # Get existing follow-ups to avoid duplicates
    result = await db.execute(
        select(FollowUp.email_id)
        .where(FollowUp.user_id == user.id, FollowUp.is_done == False)
    )
    existing_ids = {row[0] for row in result.all() if row[0]}

    # Check received emails for replies (via Gmail if connected)
    received_subjects = set()
    if user.gmail_connected:
        try:
            from services.gmail_service import fetch_recent_emails
            recent = await fetch_recent_emails(user, db, max_results=50)
            for e in recent:
                subj = (e.get("subject") or "").lower().replace("re: ", "").replace("fwd: ", "").strip()
                received_subjects.add(subj)
        except Exception as e:
            logger.warning("Gmail fetch for follow-up scan failed: %s", e)

    new_followups = []
    for email in sent_emails:
        # Skip if already tracked
        if str(email.id) in existing_ids:
            continue

        # Check if reply exists
        clean_subject = (email.subject or "").lower().replace("re: ", "").replace("fwd: ", "").strip()
        if clean_subject in received_subjects:
            continue  # Got a reply

        # Create follow-up record
        days_ago = (datetime.utcnow() - email.sent_at).days if email.sent_at else 3
        followup = FollowUp(
            user_id=user.id,
            email_id=str(email.id),
            to_email=email.recipient,
            subject=email.subject,
            sent_at=email.sent_at,
            follow_up_due=email.sent_at + timedelta(days=3) if email.sent_at else datetime.utcnow(),
        )
        db.add(followup)
        new_followups.append({
            "id": str(email.id),
            "source": "follow_up",
            "summary": f"No reply from {email.recipient}: {email.subject} ({days_ago}d ago)",
            "to_email": email.recipient,
            "subject": email.subject,
            "days_ago": days_ago,
            "urgency": 6,
            "actionable": True,
            "surface": "digest",
            "action_type": "send_reply",
            "reason": f"Sent {days_ago} days ago, no reply received",
        })

    if new_followups:
        logger.info(
            "Follow-up scan for %s: %d unreplied emails found",
            user.name, len(new_followups),
        )

    return new_followups
