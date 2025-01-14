# Imports
import logging
from rich.logging import RichHandler

# Logging
logging.basicConfig(level="NOTSET",format="%(message)s",datefmt="[%X]",handlers=[RichHandler(rich_tracebacks=True)])
log = logging.getLogger("rich")
