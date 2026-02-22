"""
Safety Classifier Module
Version: 2.0.0 - February 2026

Classifies commands and actions into safety tiers.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional


class SafetyTier(Enum):
    """Safety tier classification levels."""
    SAFE = "safe"           # Auto-execute, no risk
    MODERATE = "moderate"   # Log and execute, low risk
    ELEVATED = "elevated"   # Notify and execute, medium risk
    DANGEROUS = "dangerous" # Require confirmation, high risk


@dataclass
class CommandRule:
    """Rule for classifying commands."""
    tier: SafetyTier
    patterns: List[str]
    description: str
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []


# Default safety rules
DEFAULT_RULES = [
    # SAFE - Auto-execute (read-only, no side effects)
    CommandRule(
        SafetyTier.SAFE,
        ["ls", "cat", "head", "tail", "grep", "find", "wc", "sort", "uniq",
         "echo", "pwd", "whoami", "date", "uname", "which", "type", "file",
         "stat", "du", "df", "free", "uptime", "ps aux", "top -n 1", "htop -n 1",
         "history", "env", "printenv", "id", "groups", "hostname", "uname"],
        "Read-only system commands",
        ["ls -la", "cat file.txt", "grep pattern file.txt"]
    ),
    
    # MODERATE - Log and execute (read-only dev commands)
    CommandRule(
        SafetyTier.MODERATE,
        ["git status", "git log", "git diff", "git branch", "git remote",
         "git show", "git blame", "git rev-parse",
         "npm list", "npm outdated", "npm view",
         "pip list", "pip show", "pip freeze",
         "docker ps", "docker images", "docker logs", "docker inspect",
         "docker stats", "docker port", "docker top",
         "python --version", "python3 --version", "node --version", "npm --version",
         "git --version", "docker --version"],
        "Non-destructive development commands",
        ["git status", "docker ps -a", "npm list --depth=0"]
    ),
    
    # ELEVATED - Notify and execute (modifies files or state)
    CommandRule(
        SafetyTier.ELEVATED,
        ["git pull", "git push", "git commit", "git checkout", "git merge",
         "git add", "git rm", "git stash", "git reset", "git rebase",
         "npm install", "npm update", "npm uninstall", "npm run",
         "pip install", "pip uninstall", "pip install --upgrade",
         "docker pull", "docker run", "docker exec", "docker build",
         "docker start", "docker stop", "docker restart",
         "mkdir", "touch", "mv", "cp", "chmod", "chown",
         "tar", "zip", "unzip", "wget", "curl -O"],
        "Commands that modify files or system state",
        ["npm install package", "mkdir newdir", "git commit -m 'msg'"]
    ),
    
    # DANGEROUS - Require confirmation (destructive or system-level)
    CommandRule(
        SafetyTier.DANGEROUS,
        ["rm -rf", "rm -r", "rm -f", "rmdir",
         "sudo", "su -", "doas",
         "mkfs", "dd", "fdisk", "parted", "format",
         "chmod 777", "chmod -R 777", "chown -R",
         "> /dev/", "> /dev/sd", "> /dev/nvme",
         "kill -9", "kill -KILL", "pkill -9", "killall",
         "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
         "docker rm", "docker rmi", "docker system prune", "docker volume prune",
         "git push --force", "git reset --hard", "git clean -fd",
         "drop table", "delete from", "truncate",
         "iptables", "ufw", "firewall-cmd"],
        "Destructive or system-level commands",
        ["rm -rf directory", "sudo command", "dd if=/dev/zero"]
    ),
]

# Global rules list (can be extended)
_rules: List[CommandRule] = DEFAULT_RULES.copy()


def classify_command(command: str) -> Tuple[SafetyTier, str]:
    """
    Classify a command into a safety tier.
    
    Args:
        command: The command string to classify
        
    Returns:
        Tuple of (SafetyTier, description)
    """
    command_lower = command.lower().strip()
    
    # Check in order of danger level (most dangerous first)
    for tier in [SafetyTier.DANGEROUS, SafetyTier.ELEVATED, SafetyTier.MODERATE, SafetyTier.SAFE]:
        for rule in _rules:
            if rule.tier != tier:
                continue
                
            for pattern in rule.patterns:
                pattern_lower = pattern.lower()
                
                # For dangerous patterns, check if contained anywhere
                if tier == SafetyTier.DANGEROUS:
                    if pattern_lower in command_lower:
                        return rule.tier, rule.description
                # For other tiers, check if command starts with pattern
                elif command_lower.startswith(pattern_lower):
                    return rule.tier, rule.description
    
    # Default to ELEVATED for unknown commands
    return SafetyTier.ELEVATED, "Unknown command - requires review"


def get_all_rules() -> List[CommandRule]:
    """Get all current safety rules."""
    return _rules.copy()


def add_custom_rule(tier: SafetyTier, patterns: List[str], 
                    description: str, examples: List[str] = None) -> None:
    """
    Add a custom safety rule.
    
    Args:
        tier: Safety tier for this rule
        patterns: List of command patterns
        description: Description of the rule
        examples: Optional list of example commands
    """
    rule = CommandRule(tier, patterns, description, examples)
    _rules.append(rule)


def remove_rule(pattern: str) -> bool:
    """
    Remove a rule by pattern.
    
    Args:
        pattern: The pattern to remove
        
    Returns:
        True if rule was removed, False if not found
    """
    global _rules
    original_count = len(_rules)
    _rules = [r for r in _rules if pattern not in r.patterns]
    return len(_rules) < original_count


def is_safe(command: str) -> bool:
    """Check if a command is safe to auto-execute."""
    tier, _ = classify_command(command)
    return tier == SafetyTier.SAFE


def requires_confirmation(command: str) -> bool:
    """Check if a command requires user confirmation."""
    tier, _ = classify_command(command)
    return tier == SafetyTier.DANGEROUS


def get_tier_level(tier: SafetyTier) -> int:
    """Get numeric level for a tier (higher = more dangerous)."""
    levels = {
        SafetyTier.SAFE: 0,
        SafetyTier.MODERATE: 1,
        SafetyTier.ELEVATED: 2,
        SafetyTier.DANGEROUS: 3
    }
    return levels.get(tier, 2)


def compare_tier(tier1: SafetyTier, tier2: SafetyTier) -> int:
    """
    Compare two safety tiers.
    
    Returns:
        Negative if tier1 < tier2
        Zero if tier1 == tier2
        Positive if tier1 > tier2
    """
    return get_tier_level(tier1) - get_tier_level(tier2)