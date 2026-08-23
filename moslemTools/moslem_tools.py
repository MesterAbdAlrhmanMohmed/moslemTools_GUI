from moslem_tools.main import main_app, main
from moslem_tools.display_name import get_smart_display_name
from moslem_tools.workers import MessageCheckWorker
from moslem_tools.startup_checks import check_missed_khatmah_alert, show_random_quote_message, run_startup_checks

if __name__ == "__main__":
    main_app()
