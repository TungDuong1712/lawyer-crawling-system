from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.lawyers.models import RocketReachContact
import csv
from pathlib import Path
from datetime import datetime


class Command(BaseCommand):
    help = "Export RocketReachContact data to a CSV file with specific columns"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            required=True,
            help="Absolute or relative path to the output CSV file",
        )
        parser.add_argument(
            "--status",
            type=str,
            default=None,
            help="Optional status filter (e.g., active, bounced, invalid, unknown)",
        )

    def handle(self, *args, **options):
        output_raw = Path(options["output"]).expanduser().resolve()

        # Allow passing a directory as --output; generate a filename automatically
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        if output_raw.exists() and output_raw.is_dir():
            output_path = output_raw / f"rocketreach_contacts_{timestamp}.csv"
        elif output_raw.suffix.lower() != ".csv":
            # Treat as directory-like path without .csv suffix
            output_path = output_raw / f"rocketreach_contacts_{timestamp}.csv"
        else:
            output_path = output_raw

        output_path.parent.mkdir(parents=True, exist_ok=True)

        queryset = RocketReachContact.objects.all()
        if options.get("status"):
            queryset = queryset.filter(status=options["status"]) 

        headers = [
            "id",
            "points",
            "last_active",
            "title",
            "firstname",
            "lastname",
            "company",
            "position",
            "email",
            "phone",
            "mobile",
            "address1",
            "address2",
            "city",
            "state",
            "zipcode",
            "timezone",
            "country",
            "fax",
            "preferred_locale",
            "attribution_date",
            "attribution",
            "website",
            "facebook",
            "foursquare",
            "instagram",
            "linkedin",
            "skype",
            "twitter",
            "stage",
        ]

        def split_name(full_name: str):
            if not full_name:
                return "", ""
            parts = full_name.strip().split()
            if len(parts) == 1:
                return parts[0], ""
            return parts[0], " ".join(parts[1:])

        now_iso = timezone.now().isoformat()

        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for contact in queryset.iterator(chunk_size=1000):
                first_name, last_name = split_name(contact.name)

                # Prefer explicit primary_email if present, fallback to email
                email_value = contact.primary_email or contact.email or ""

                row = {
                    "id": contact.profile_id,
                    "points": "",
                    "last_active": (contact.last_verified or contact.updated_at or None),
                    "title": contact.title or "",
                    "firstname": first_name,
                    "lastname": last_name,
                    "company": contact.company or "",
                    "position": contact.title or "",
                    "email": email_value,
                    "phone": contact.phone or "",
                    "mobile": "",
                    "address1": "",
                    "address2": "",
                    "city": "",
                    "state": "",
                    "zipcode": "",
                    "timezone": "",
                    "country": "",
                    "fax": "",
                    "preferred_locale": "",
                    "attribution_date": contact.created_at.isoformat() if contact.created_at else now_iso,
                    "attribution": "RocketReach",
                    "website": "",
                    "facebook": "",
                    "foursquare": "",
                    "instagram": "",
                    "linkedin": contact.linkedin_url or "",
                    "skype": "",
                    "twitter": contact.twitter_url or "",
                    "stage": contact.status or "",
                }

                # Ensure datetime values become ISO strings
                if isinstance(row["last_active"], datetime):
                    row["last_active"] = row["last_active"].isoformat()

                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f"Exported {queryset.count()} contacts to {output_path}"))
