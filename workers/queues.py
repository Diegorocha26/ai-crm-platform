QUEUE_SCRAPE = "scrape"
QUEUE_ENRICH = "enrich"
QUEUE_EMBED = "embed"
QUEUE_DLQ = "dead_letter"

# Job timeout and retry config per queue
QUEUE_CONFIG = {
    QUEUE_SCRAPE: {"timeout": 60, "retry": 3},
    QUEUE_ENRICH: {"timeout": 120, "retry": 2},
    QUEUE_EMBED:  {"timeout": 30, "retry": 3},
}
