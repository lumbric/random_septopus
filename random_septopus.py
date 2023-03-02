import math
import time
import logging
import serial
import datetime

import logging_config

serial_port = "/dev/ttyACM0"


DRINKS = [
    # Bottles: Vodka, Gin, Water, Apple,  Makava, Cranberry, Orange
    [40, 0, 0, 0, 140, 0, 0],  # 40g Vodka + 140g Makava
    [40, 0, 0, 0, 0, 0, 140],  # 40g Vodka + 140g Orange
    [0, 40, 0, 0, 0, 0, 140],  # 40g Gin + 140g Orange
    [0, 40, 0, 0, 140, 0, 0],  # 40g Gin + 140g Makava
    [40, 0, 0, 0, 0, 30, 110],  # 40g Vodka + 30g Cranberry + 110g Orange
    [0, 0, 0, 150, 0, 30, 0],  # 150g Apple + 30g Cranberry
    [0, 0, 0, 0, 0, 40, 140],  # 40g Cranberry + 140g Orange
    [0, 0, 0, 180, 0, 0, 0],  # Water
    [40, 0, 0, 140, 0, 0, 0],  # 40g Vodka + 140g Water
    [30, 30, 30, 0, 30, 30, 30],  # A bit of everything
    [0, 0, 0, 180, 0, 0, 0],  # Water
    [0, 40, 0, 0, 0, 30, 110],  # 40g Gin + 30g Cranberry + 110g Orange
    [0, 0, 0, 180, 0, 0, 0],  # Water
    [0, 0, 0, 0, 0, 40, 140],  # 40g Cranberry + 140g Orange
    [40, 0, 0, 0, 0, 30, 110],  # 40g Vodka + 30g Cranberry + 110g Orange
    [0, 0, 0, 180, 0, 0, 0],  # Water
    [40, 0, 0, 140, 0, 0, 0],  # 40g Vodka + 140g Apple
    [0, 40, 0, 140, 0, 0, 0],  # 40g Gin + 140g Apple
    [0, 40, 0, 0, 0, 0, 140],  # 40g Gin + 140g Orange
    [0, 40, 0, 0, 0, 140, 0],  # 40g Gin + 140g Cranberry
]


def send(serial_connection, command, *args):
    command_with_args = command + " " + " ".join(str(n) for n in args)
    serial_connection.write((command_with_args + "\r\n").encode("ISO-8859-1"))
    logging.debug("Sent: %s \\r\\n" % command_with_args)
    serial_connection.flushInput()


def pour(serial_connection):
    now = datetime.datetime.now()
    hourly_repetitions = math.ceil(60 / len(DRINKS))
    if 60 % len(DRINKS) != 0:
        logging.warning(
            f"number of drinks {len(DRINKS)} not a divider of 60, will skip some drinks"
        )
    drink = DRINKS[now.minute % hourly_repetitions]

    logging.info(f"Pouring... {drink}")
    args = (str(arg) for arg in drink)
    send(serial_connection, "POUR", *args)


def main():
    logging_config.setup_logging()

    logging.info("Starting...")

    while True:
        try:
            serial_connection = serial.Serial(serial_port, 9600)
        except Exception as e:
            logging.error(
                f"Could not establish serial connection on port {serial_port}:\n {str(e)}"
            )
            time.sleep(2)
        else:
            break

    logging.info("Serial connection established, starting main loop!")

    try:
        main_loop(serial_connection)
    finally:
        serial_connection.close()


def main_loop(serial_connection):
    serial_buffer = ""
    commands = []
    last_idle_logmsg = 0

    while True:
        IDLE_LOG_MSG_INTERVAL = 2
        if time.time() - last_idle_logmsg > IDLE_LOG_MSG_INTERVAL:
            logging.info(f"Waiting for READY and CUP...")

            logging.debug(f"Serial buffer: {serial_buffer}")
            last_idle_logmsg = time.time()

        try:
            serial_buffer += serial_connection.read().decode("ISO-8859-1")
            commands = serial_buffer.split("\r\n")
            serial_buffer = commands.pop()

            for command in commands:
                logging.debug("Command: %s \\r\\n" % command)

                command_parts = command.split(" ")

                if command_parts[0] == "READY" and int(command_parts[2]) == 1:
                    # ready and cup there
                    pour(serial_connection)

            time.sleep(20e-3)

        except Exception as e:
            logging.exception(str(e) + "\n")


if __name__ == "__main__":
    main()
