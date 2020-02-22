#!/usr/bin/env python

import bluetooth
import os
import sys
from xml.etree import ElementTree
from PyOBEX import client, responses


def byte_to_megabyte(num: float) -> float:
    return num * 0.000001


def byte_to_kilobyte(num: float) -> float:
    return num * 0.001


if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.stderr.write(f"Usage: {sys.argv[0]} <device address>")
        sys.exit(1)

    device_address = sys.argv[1]

    services = bluetooth.find_service(uuid="1106", address=device_address)
    if services:
        port = services[0]["port"]
    else:
        sys.stderr.write("Bluetooth service is not enabled!")
        sys.exit()

    c = client.BrowserClient(device_address, port)

    # Connect
    response = c.connect()
    if not isinstance(response, responses.ConnectSuccess):
        sys.stderr.write("Failed to connect.\n")
        sys.exit(1)

    current_path: str = "."  # root directory

    while True:
        # Open this directory
        if current_path == "..":
            response = c.setpath(to_parent=True)
        else:
            response = c.setpath(current_path)
        if isinstance(response, responses.FailureResponse):
            sys.stderr.write(
                "Failed to enter directory. Make sure the directory is exists.\n")
            sys.exit(1)

        # List the directory
        headers, data = c.listdir()
        tree = ElementTree.fromstring(data)
        for element in tree.findall("folder"):
            name = element.attrib["name"]
            print(f"{name}/")

        # List the file
        for element in tree.findall("file"):
            name = element.attrib["name"]
            byte_size: float = float(element.attrib["size"])
            megabyte_size: float = byte_to_megabyte(byte_size)
            size: str = ""
            if megabyte_size >= 0.1:
                size = f"{megabyte_size:.2f} MB"
            else:
                kilobyte_size: float = byte_to_kilobyte(byte_size)
                size = f"{kilobyte_size:.2f} KB"

            print(f"{name} — {size}")

        command: str = input()
        tokens: [str] = command.split()

        current_path = "."

        # Navigate to
        # cd test/
        if tokens[0] == "cd":
            current_path = tokens[1]
        # Download
        # dl test.txt
        elif tokens[0] == "dl":
            name: str = tokens[1]
            output_filename: str = name

            try:
                output_filename = tokens[2]
            except IndexError:
                pass

            print(f"Downloading file {name}")
            response = c.get(name)
            if isinstance(response, responses.FailureResponse):
                sys.stderr.write(f"Failed to get {name}!")
            else:
                print(f"Writing file to {name}")
                headers, data = response
                try:
                    open(output_filename, "wb").write(data)
                except IOError:
                    sys.stderr.write(f"Failed to write file to {name}")
        # Show file
        # cat test.txt
        elif tokens[0] == "cat":
            name: str = tokens[1]

            print(f"Downloading file {name}")
            response = c.get(name)
            if isinstance(response, responses.FailureResponse):
                sys.stderr.write(f"Failed to get {name}!")
            else:
                print(response[1])

    c.disconnect()
    sys.exit()

