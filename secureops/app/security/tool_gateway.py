import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from app.adapters.base import NormalizedToolCall
from app.security.network import validate_destination_url

logger = logging.getLogger(__name__)

# Dangerous shell command injection patterns
DANGEROUS_COMMAND_PATTERNS = [
    re.compile(r"[|;&`$]"),
    re.compile(r"\$\("),
    re.compile(r"cat\s+/etc/"),
    re.compile(r"rm\s+-rf"),
]

# Dangerous path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\.[/\\]"),
    re.compile(r"[/\\]etc[/\\]passwd"),
    re.compile(r"[/\\]etc[/\\]shadow"),
    re.compile(r"c:[/\\]windows", re.IGNORECASE),
]

# Destructive operations requiring Human-In-The-Loop approval
DESTRUCTIVE_TOOLS = {"delete_data", "drop_table", "wipe_database", "purge_logs", "reset_system"}


class ToolSecurityGateway:
    def validate_tool_call(
        self,
        tool_call: NormalizedToolCall,
        allowed_tools: List[str],
        agent_id: str,
        tenant_id: str,
        user_id: Optional[str] = None,
    ) -> Tuple[str, str, float]:
        """
        Validates a normalized tool call against deterministic security policy rules.
        Returns Tuple of (Decision ["ALLOW", "REQUIRE_APPROVAL", "BLOCK"], Reason, RiskScoreContribution).
        """
        tool_name = tool_call.tool_name.strip()
        args = tool_call.arguments or {}

        # 1. Tool Allowlist Check
        if allowed_tools and tool_name not in allowed_tools:
            logger.warning(f"Unauthorized tool invocation '{tool_name}' for agent '{agent_id}' (allowed: {allowed_tools})")
            return "BLOCK", f"Tool '{tool_name}' is not on the authorized allowlist for agent '{agent_id}'", 0.9

        # Convert all argument values to strings for inspection
        args_str = self._stringify_args(args)

        # 2. Command Injection Check
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if pattern.search(args_str):
                logger.warning(f"Command injection pattern detected in tool '{tool_name}' arguments: {args_str}")
                return "BLOCK", "Security Violation: Command injection pattern detected in tool arguments", 1.0

        # 3. Path Traversal Check
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern.search(args_str):
                logger.warning(f"Path traversal pattern detected in tool '{tool_name}' arguments: {args_str}")
                return "BLOCK", "Security Violation: Path traversal pattern detected in tool arguments", 0.9

        # 4. SSRF URL Check
        url_arg = args.get("url") or args.get("endpoint") or args.get("target")
        if isinstance(url_arg, str) and url_arg.startswith(("http://", "https://")):
            is_safe, error_msg = validate_destination_url(url_arg)
            if not is_safe:
                logger.warning(f"SSRF URL violation in tool '{tool_name}': {error_msg}")
                return "BLOCK", f"Security Violation: SSRF URL rejected ({error_msg})", 1.0

        # 5. Destructive Operations -> Require HITL Approval
        if tool_name.lower() in DESTRUCTIVE_TOOLS:
            logger.info(f"Destructive tool '{tool_name}' requested by agent '{agent_id}'; triggering HITL approval")
            return "REQUIRE_APPROVAL", f"Destructive tool '{tool_name}' requires Human-In-The-Loop approval", 0.7

        return "ALLOW", f"Tool '{tool_name}' authorized and validated cleanly", 0.1

    def _stringify_args(self, args: Dict[str, Any]) -> str:
        parts = []
        for k, v in args.items():
            parts.append(f"{k}={v}")
        return " ".join(parts)


tool_security_gateway = ToolSecurityGateway()
