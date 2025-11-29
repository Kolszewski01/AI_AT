"""
AI Trading System - Desktop Application
Main entry point
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.components.main_window import MainWindow
from src.utils.config import Config
from src.utils.logger import setup_logger, get_logger


def main():
    """Main application entry point"""
    # Setup logging first
    setup_logger()
    logger = get_logger("main")
    logger.info("=" * 60)
    logger.info("AI Trading System - Starting")
    logger.info("=" * 60)

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Trading System")
    app.setOrganizationName("Sebastian2103")
    logger.info("QApplication created")

    # Load configuration
    config = Config()
    logger.info(f"Configuration loaded: {config}")

    # Create and show main window
    try:
        window = MainWindow(config)
        window.show()
        logger.info("Main window displayed")
    except Exception as e:
        logger.exception(f"Failed to create main window: {e}")
        sys.exit(1)

    # Start event loop
    logger.info("Starting event loop")
    exit_code = app.exec()
    logger.info(f"Application exiting with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
