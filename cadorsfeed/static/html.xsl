<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:a="http://www.w3.org/2005/Atom"
                xmlns:h="http://www.w3.org/1999/xhtml"
                version="1.0">
  <xsl:output method="xml" omit-xml-declaration="no" encoding="UTF-8"
	      indent="yes" media-type="application/xml+xhtml"/>
  
  <xsl:template match="/a:feed">
    <h:html>
      <h:head>
	<h:title><xsl:value-of select="a:title/text()"/></h:title>
      </h:head>
      <h:body>
	<h:div>
	  <h:header><h:h1><xsl:value-of select="a:title"/></h:h1></h:header>
	  <h:div>
	    <xsl:apply-templates select="a:entry" />
	  </h:div>
	  <h:footer><h:p><xsl:value-of select="a:rights"/></h:p></h:footer>
	</h:div>
      </h:body>
    </h:html>
  </xsl:template>
  
  <xsl:template match="a:entry">
    <h:article>
      <h:h2><h:a><xsl:attribute name="href"><xsl:value-of select="a:link/@href"/></xsl:attribute><xsl:value-of select="a:title"/></h:a></h:h2>
      <h:p>
        <h:ul>
          <xsl:apply-templates select="a:category" />
        </h:ul>
        <h:br />
        <h:ul>
          <xsl:apply-templates select="a:author" />
        </h:ul>
        <h:br />
        <xsl:value-of select="a:updated"/>
      </h:p>
      <xsl:copy-of select="a:content/*"/>
    </h:article>
  </xsl:template>
  
  <xsl:template match="a:author">
    <h:li><xsl:value-of select="a:name"/></h:li>
  </xsl:template>
  
  <xsl:template match="a:category">
    <h:li><xsl:value-of select="@label" /></h:li>
  </xsl:template>
  
</xsl:stylesheet>