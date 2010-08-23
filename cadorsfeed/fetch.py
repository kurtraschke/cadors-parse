import mechanize
import re


def fetchLatest():
    br = mechanize.Browser()
    br.open("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/nrpt.aspx?lang=eng")
    br.select_form(name="pageForm")
    latestDate = br["txt_ReportDate"]
    return latestDate


def fetchReport(reportDate):
    br = mechanize.Browser()
    br.open("http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/nrpt.aspx?lang=eng")
    br.select_form(name="pageForm")
    br["txt_ReportDate"] = reportDate
    response2 = br.submit(name="btn_SearchTop")
    data = response2.get_data()
    data_filtered = re.sub("""<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="[A-Za-z0-9/+=]*" />""",
                           "<!-- viewstate field stripped -->",
                           data)
    return data_filtered.decode("utf-8")
