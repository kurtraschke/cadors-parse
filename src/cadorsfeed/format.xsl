<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                xmlns:a="http://www.w3.org/2005/Atom"
                xmlns:h="http://www.w3.org/1999/xhtml" 
                xmlns:pyf="urn:uuid:fb23f64b-3c54-4009-b64d-cc411bd446dd"
                version="1.0" exclude-result-prefixes="pyf">
  <xsl:output method="xml" omit-xml-declaration="no" encoding="UTF-8"
              indent="yes"/>
  
  <xsl:template match="/">   
    <a:feed>
      <a:updated><xsl:value-of select="$ts" /></a:updated>
      <a:id>urn:uuid:ec421c3e-df93-4e96-bc2c-81156167830b</a:id>
      <a:title>CADORS National Report</a:title>
      <a:rights>
	Transport Canada endeavours to ensure the accuracy and integrity of the data contained within CADORS, however, the information within should be treated as preliminary, unsubstantiated and subject to change. This is an unofficial reproduction of data contained within CADORS and was not produced in affiliation with nor with the endorsement of Transport Canada.
      </a:rights>
      <xsl:for-each select="//h:div[@class = 'pagebreak']">
	<a:entry>
	  <xsl:variable name="cadors-number">
	    <xsl:value-of select="pyf:strip_nbsp((.//h:th[contains(text(),'Cadors Number:')]/following-sibling::h:td/h:strong/text()))"/>
	  </xsl:variable>
	  <a:title>CADORS Report <xsl:value-of select="$cadors-number"/></a:title>
	  <a:link rel="alternate" type="text/html">
	    <xsl:attribute name="href">
	      <xsl:variable name="base-url"><![CDATA[http://wwwapps.tc.gc.ca/Saf-Sec-Sur/2/cadors-screaq/qs.aspx?lang=eng&cadorsno=]]></xsl:variable>
	      <xsl:value-of select="concat($base-url,$cadors-number)" />
	    </xsl:attribute>
	  </a:link>
	  <xsl:variable name="date">
	    <xsl:value-of select=".//h:th[contains(text(),'Occurrence Date:')]/following-sibling::h:td/h:strong/text()"/>
	  </xsl:variable>
	  <xsl:variable name="time">
	    <xsl:value-of select=".//h:th[contains(text(),'Occurrence Time:')]/following-sibling::h:td/h:strong/text()"/>
	  </xsl:variable>
	  <a:updated>
	    <xsl:value-of select="pyf:fix_datetime($date, $time)" />
	  </a:updated>
	  <xsl:for-each select="pyf:fix_names(.//h:th[contains(text(),'User Name:')]/following-sibling::h:td/h:strong/text())">
	    <a:author>
	      <a:name>
		<xsl:value-of select="."/>
	      </a:name>
	    </a:author>
	  </xsl:for-each>
	  <a:id><xsl:value-of select="pyf:produce_id($cadors-number)" /></a:id>
	  <a:content type="xhtml">
	    <h:div>
	      <xsl:copy-of select="pyf:content(.//h:th[contains(text(),'Narrative:')]/following-sibling::h:td/h:strong/text())" />
	    </h:div>
	  </a:content>
	  
	  <xsl:for-each select=".//h:fieldset/h:legend/h:strong[contains(text(),'Event Information')]/../following-sibling::h:table//h:strong/text()">
	    <a:category>
	      <xsl:attribute name="term">
		<xsl:value-of select="." />
	      </xsl:attribute>
	      
	      <xsl:attribute name="label">
		<xsl:value-of select="." />
	      </xsl:attribute>
	    </a:category>
	  </xsl:for-each>
	</a:entry>
      </xsl:for-each>
    </a:feed>
  </xsl:template>
</xsl:stylesheet>
