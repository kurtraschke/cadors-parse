import mechanize
import re

def fetch_latest_date():
    br = mechanize.Browser()
    br.open("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/nrpt.aspx?lang=eng")
    br.select_form(name="pageForm")
    latest_date = br["txt_ReportDate"]
    return latest_date

def fetch_daily_report(report_date):
    br = mechanize.Browser()
    br.open("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/nrpt.aspx?lang=eng")
    br.select_form(name="pageForm")
    br["txt_ReportDate"] = report_date
    response2 = br.submit(name="btn_SearchTop")
    if not response2.geturl().startswith("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/rpt.aspx"):
        raise ReportFetchError()
    data = response2.get_data()
    if re.search("There were no results for the search criteria you entered",
                 data):
        raise ReportNotFoundError()
    data_filtered = re.sub("""<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="[A-Za-z0-9/+=]*" />""",
                           "<!-- viewstate field stripped -->",
                           data)
    return data_filtered.decode("utf-8")

class ReportNotFoundError(Exception):
    pass


class ReportFetchError(Exception):
    pass
