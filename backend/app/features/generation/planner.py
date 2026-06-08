"""Decides which campaigns to generate for a company + event combination."""


class CampaignPlanner:
    def plan(self, company_profile: dict, event: dict) -> list[dict]:
        """Return a list of campaign specs (theme, format, etc.)."""
        raise NotImplementedError
