import logging

def setup_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    app.logger.setLevel(logging.INFO)
