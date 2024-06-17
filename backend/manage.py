import os
import sys


def main() -> None:
	from dotenv import load_dotenv

	load_dotenv()
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
	if not os.environ.get("DJANGO_CONFIGURATION", None):
		os.environ.setdefault("DJANGO_CONFIGURATION", "Development")
		# os.system("mypy .")

	try:
		from configurations.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError(
			"Couldn't import Django. Are you sure it's installed and "
			"available on your PYTHONPATH environment variable? Did you "
			"forget to activate a.txt virtual environment?"
		) from exc
	execute_from_command_line(sys.argv)


if __name__ == "__main__":
	main()
