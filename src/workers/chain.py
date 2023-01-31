from time import sleep
import logging


def run_chain_worker(queue_provider, metadata_processor, delay=2 * 60):
    while True:
        try:
            logging.info("in iteration of loop")
            record = queue_provider.next()

            if record is not None:
                metadata_processor.process_metadata_entry(
                    record["tx_hash"], record["json_metadata"]
                )
                queue_provider.ack(record["tx_hash"])
            else:
                sleep(delay)
        except Exception as ex:
            logging.warning(f"exception in processing loop {ex}")
            raise ex

        logging.info("Chain Worker BEEP!")
