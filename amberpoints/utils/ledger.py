from amberpoints.config import config
from amberpoints.env import env
from amberpoints.tables import AuditLog
from amberpoints.utils.logging import send_heartbeat


async def create_ledger_entry(
    performer: str,
    target_user: str,
    action: str,
    amount: int | None = None,
    reason: str | None = None,
):
    await AuditLog.insert(
        AuditLog(
            user_id=performer,
            action=action,
            target_user=target_user,
            amount=amount,
            reason=reason,
        )
    )
    if config.slack.ledger_channel:
        message = f"*Ledger Entry*\n*Action:* {action}\n*Performer:* <@{performer}>\n*Target User:* <@{target_user}>"
        if amount is not None:
            message += f"\n*Amount:* {amount}"
        if reason:
            message += f"\n*Reason:* {reason}"
        try:
            await env.app.chat_postMessage(
                channel=config.slack.ledger_channel,
                text=message,
            )
        except Exception:
            await send_heartbeat(
                "Failed to post ledger entry to Slack channel.", production=True
            )
