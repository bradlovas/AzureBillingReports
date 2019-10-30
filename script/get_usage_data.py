#!/usr/bin/python
"""Script to fetch latest monthly billing data and price sheet."""
import sys
import datetime
import time
import requests


STATUS_QUEUED = 1
STATUS_IN_PROGRESS = 2
STATUS_COMPLETED = 3
STATUS_FAILED = 4
STATUS_NO_DATA_FOUND = 5
STATUS_READY_TO_DOWNLOAD = 6
STATUS_TIMED_OUT = 7

HOST_NAME = "https://consumption.azure.com"
API_PATH = "/v3/enrollments/%s/usagedetails/submit?startTime=%s&endTime=%s"


def get_usage_uri(eid, start_date, end_date):
    """Build usage uri from eid and start and end dates."""
    path_url = HOST_NAME + API_PATH
    uri = path_url % (eid, start_date, end_date)
    return uri


def get_most_data_uri(eid):
    """Build usage uri from eid for the past three years."""
    dte = datetime.datetime.now()
    start_date = (dte - datetime.timedelta(36 * 365 / 12)).strftime("%Y-%m-01")
    end_date = dte.strftime("%Y-%m-%d")
    return get_usage_uri(eid, start_date, end_date)


def get_current_month_uri(eid):
    """Build usage uri from eid for the current month."""
    dte = datetime.datetime.now()
    start_date = dte.strftime("%Y-%m-01")
    end_date = dte.strftime("%Y-%m-%d")
    return get_usage_uri(eid, start_date, end_date)


def get_previous_30_days_uri(eid):
    """Build usage uri starting with the first of the previous month."""
    dte = datetime.datetime.now()
    start_date = (dte - datetime.timedelta(1 * 365 / 12)).strftime("%Y-%m-01")
    end_date = dte.strftime("%Y-%m-%d")
    return get_usage_uri(eid, start_date, end_date)


def get_previous_6_months_uri(eid):
    """Build usage uri for the previous 6 months."""
    dte = datetime.datetime.now()
    start_date = (dte - datetime.timedelta(6 * 365 / 12)).strftime("%Y-%m-01")
    end_date = dte.strftime("%Y-%m-%d")
    return get_usage_uri(eid, start_date, end_date)


def get_previous_12_months_uri(eid):
    """Build usage uri for the previous 12 months."""
    dte = datetime.datetime.now()
    start_date = (dte - datetime.timedelta(12 * 365 / 12)).strftime("%Y-%m-01")
    end_date = dte.strftime("%Y-%m-%d")
    return get_usage_uri(eid, start_date, end_date)


def download_file(url, dte):
    """Download usage report with shared access key based URL."""
    local_filename = "usage-%s.csv" % (dte.isoformat())
    local_filename = local_filename.replace(":", "-")
    # NOTE the stream=True parameter
    response = requests.get(url, stream=True)
    with open(local_filename, "wb") as csvfile:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                csvfile.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian
    return local_filename


def get_status(uri, auth_key, count, is_report_url=False):
    """Submit request and poll for shared access key based URL."""
    print("[" + str(count) + "] Calling uri " + uri)

    headers = {
        "authorization": "bearer " + str(auth_key),
        "Content-Type": "application/json",
    }

    if is_report_url:
        resp = requests.get(uri, headers=headers,)
    else:
        resp = requests.post(uri, headers=headers,)

    if resp.status_code == 200 or resp.status_code == 202:

        status = resp.json()["status"]
        report_url = resp.json()["reportUrl"]

        if status == STATUS_QUEUED:

            print("Queued.")
            print(report_url)

            # Wait a few secs and check again
            time.sleep(10)
            get_status(report_url, auth_key, count + 1, True)

        elif status == STATUS_IN_PROGRESS:

            print("In Progress.")
            print(report_url)

            # Wait a few secs and check again
            time.sleep(10)
            get_status(report_url, auth_key, count + 1, True)

        elif status == STATUS_COMPLETED:

            print("Completed.")
            blob_path = resp.json()["blobPath"]
            print(blob_path)

            print("download blob")
            download_file(blob_path, datetime.datetime.now())

        elif status == STATUS_FAILED:

            print("Failed.")

        elif status == STATUS_NO_DATA_FOUND:

            print("No Data Found.")

        elif status == STATUS_READY_TO_DOWNLOAD:

            print("Ready to download.")
            blob_path = resp.json()["blobPath"]
            print(blob_path)

            # Download Blob
            print("download blob")
            download_file(blob_path, datetime.datetime.now())

        elif status == STATUS_TIMED_OUT:

            print("Timed out.")

        else:

            print("Unknown Status.")
    else:
        print("Error calling uri")
        print(resp.status_code)
        print(resp.text)


def main(argv):
    """Get previous 30 days usage and latest pricing."""
    eid = argv[0]
    auth_key = argv[1]

    uri = get_previous_6_months_uri(eid)
    get_status(uri, auth_key, 0)


if __name__ == "__main__":
    main(sys.argv[1:])
