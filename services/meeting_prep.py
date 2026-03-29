"""
Meeting prep service — generates 3-bullet briefs before upcoming meetings.

Runs every 5 minutes via APScheduler.
For each user with calendar connected:
1. Check for events starting in 25-35 minutes
2. Fetch recent emails with attendees
3. Call Perplexity for attendee/topic background (falls back to Claude)
4. Call Claude with meeting prep prompt
5. Push notification with the brief
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, AgentActivity, ThreadMessage
from prompts.meeting_prep import MEETING_PREP_SYSTEM
from services.calendar_service import fetch_upcoming_events
from services.claude_service import generate
from services.model_router import route
from services.push_service import send_push

logger = logging.getLogger("axis.meeting_prep")


async def _fetch_attendee_emails(user: User, attendees: list[dict], db: AsyncSession) -> str:
    """Fetch recent emails involving meeting attendees."""
    if not attendees or not user.gmail_connected:
        return "No recent email context with attendees."

    from services.gmail_service import fetch_recent_emails

    attendee_emails = [a.get("email", "") for a in attendees if a.get("email")]
    if not attendee_emails:
        return "No attendee emails available."

    # Fetch recent emails and filter for attendee matches
    emails = await fetch_recent_emails(user, db, max_results=50)
    relevant = []
    for e in emails:
        sender = (e.get("from") or "").lower()
        if any(addr.lower() in sender for addr in attendee_emails):
            relevant.append(f"From: {e['from']} | Subject: {e.get('subject', '')} | {e.get('snippet', '')[:150]}")

    if not relevant:
        return "No recent emails found with these attendees."

    return "\n".join(relevant[:5])


async def _research_background(meeting_title: str, attendees: list[dict]) -> str:
    """Call Perplexity for attendee/topic background. Falls back to Claude."""
    attendee_names = [a.get("name", a.get("email", "")) for a in attendees[:3]]
    query = f"Brief professional background: {', '.join(attendee_names)}. Context: upcoming meeting about {meeting_title}"

    try:
        result = await route(
            task_type="person_lookup",
            system="You are a research assistant. Provide brief, factual professional background on the people mentioned. 2-3 sentences each. If you cannot find information, say so.",
            user_msg=query,
            max_tokens=512,
        )
        return result["text"]
    except Exception as e:
        logger.warning("Perplexity research failed, falling back to Claude: %s", e)
        try:
            return await generate(
                system_prompt="Provide any context you can about these attendees based on their names and email domains. Be brief.",
                user_message=query,
                max_tokens=256,
            )
        except Exception:
            return "No background research available."


async def prep_meeting(user: User, event: dict, db: AsyncSession) -> str | None:
    """Generate a meeting prep brief for a single event."""
    attendees = event.get("attendees", [])
    meeting_title = event.get("summary", "Untitled meeting")

    # Fetch email context and research in sequence (research depends on attendee data)
    email_context = await _fetch_attendee_emails(user, attendees, db)
    research_context = await _research_background(meeting_title, attendees)

    attendees_text = ", ".join(
        a.get("name") or a.get("email", "unknown") for a in attendees[:8]
    ) or "No attendees listed"

    prompt = MEETING_PREP_SYSTEM.format(
        name=user.name or "there",
        meeting_title=meeting_title,
        meeting_time=event.get("start_dt", ""),
        meeting_location=event.get("location", "No location"),
        attendees=attendees_text,
        email_context=email_context,
        research_context=research_context,
    )

    brief = await generate(
        system_prompt="You are Axis. Return only the 3-bullet meeting brief. No markdown fences.",
        user_message=prompt,
        max_tokens=300,
    )

    return brief.strip() if brief else None


async def run_meeting_prep(db: AsyncSession) -> list[dict]:
    """Check all calendar-connected users for meetings starting in 25-35 minutes."""
    result = await db.execute(
        select(User).where(User.calendar_connected == True)
    )
    users = result.scalars().all()

    if not users:
        return []

    results = []
    now = datetime.utcnow()

    for user in users:
        try:
            # Fetch events in the next hour
            events = await fetch_upcoming_events(user, db, hours_ahead=1, max_results=5)

            for event in events:
                start_str = event.get("start_dt", "")
                if not start_str or event.get("is_all_day"):
                    continue

                # Parse start time
                try:
                    # Handle both formats: 2026-03-29T10:00:00+10:00 and 2026-03-29T00:00:00Z
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    start_utc = start_dt.replace(tzinfo=None) if start_dt.tzinfo is None else start_dt.astimezone(tz=None).replace(tzinfo=None)
                except (ValueError, TypeError):
                    continue

                minutes_until = (start_utc - now).total_seconds() / 60

                # Only prep for events 25-35 minutes away
                if not (25 <= minutes_until <= 35):
                    continue

                logger.info(
                    "Meeting prep triggered for %s: '%s' in %.0f min",
                    user.name, event.get("summary", ""), minutes_until,
                )

                brief = await prep_meeting(user, event, db)
                if not brief:
                    continue

                # Save as thread message
                msg = ThreadMessage(
                    user_id=user.id,
                    role="assistant",
                    content=f"**Meeting prep: {event['summary']}**\n\n{brief}",
                    message_type="intel",
                    source_skill="meeting_prep",
                )
                db.add(msg)

                # Push notification
                if user.apns_token:
                    await send_push(
                        user.apns_token,
                        f"Meeting in {int(minutes_until)}min: {event['summary'][:40]}",
                        brief[:150],
                        data={"action_type": "meeting_prep", "event_id": event.get("id", "")},
                    )

                # Log activity
                db.add(AgentActivity(
                    user_id=user.id,
                    skill="meeting_prep",
                    action="brief_generated",
                    detail=f"Meeting: {event['summary']} at {start_str}",
                    result=brief[:500],
                ))

                results.append({
                    "user_id": str(user.id),
                    "event": event["summary"],
                    "minutes_until": int(minutes_until),
                })

            await db.commit()

        except Exception as e:
            logger.error("Meeting prep failed for user %s: %s", user.id, e)

    logger.info("Meeting prep complete: %d briefs generated", len(results))
    return results
