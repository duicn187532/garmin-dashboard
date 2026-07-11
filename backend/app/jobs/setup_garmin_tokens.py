from getpass import getpass
from pathlib import Path

from ..config import get_settings


def main() -> None:
    settings = get_settings()
    try:
        from garminconnect import Garmin  # type: ignore
    except ImportError as exc:
        raise SystemExit("Install optional dependencies first: pip install garminconnect garth") from exc

    email = settings.garmin_email or input("Garmin email: ").strip()
    password = settings.garmin_password or getpass("Garmin password: ")
    tokenstore = settings.garmin_tokenstore
    Path(tokenstore).mkdir(parents=True, exist_ok=True)

    def prompt_mfa() -> str:
        return settings.garmin_mfa_code or input("Garmin MFA code: ").strip()

    client = Garmin(email, password, prompt_mfa=prompt_mfa)
    client.login(tokenstore=tokenstore)
    print(f"Garmin tokenstore ready: {tokenstore}")


if __name__ == "__main__":
    main()
