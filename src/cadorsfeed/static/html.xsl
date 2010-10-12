<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:a="http://www.w3.org/2005/Atom"
                xmlns:h="http://www.w3.org/1999/xhtml"
                version="1.0" exclude-result-prefixes="h a">
  <xsl:output method="html" omit-xml-declaration="no" encoding="UTF-8"
	      indent="yes" media-type="text/html" 
              doctype-public="XSLT-compat" />
  

  <xsl:template match="/a:feed">
    <html>
      <head>
	<title><xsl:value-of select="a:title/text()"/></title>
	<xsl:text disable-output-escaping="yes"><![CDATA[<!--[if IE]>]]></xsl:text>
	<script src="http://html5shim.googlecode.com/svn/trunk/html5.js" />
	<xsl:text disable-output-escaping="yes"><![CDATA[<![endif]-->]]></xsl:text>
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js" />
        <script src="http://cdn.jquerytools.org/1.2.5/tiny/jquery.tools.min.js"></script>
        <script type="text/javascript" src="http://www.google.com/jsapi" />
        <script type="text/javascript" src="/static/js/script.js" />  
        <link rel="stylesheet" type="text/css" href="/static/css/tabs.css" />
      </head>
      <body>
	<div>
	  <header><h1><xsl:value-of select="a:title"/></h1></header>
	  <div>
	    <xsl:apply-templates select="a:entry" />
	  </div>
	  <footer><p><xsl:value-of select="a:rights"/></p></footer>
	</div>
      </body>
    </html>
  </xsl:template>
  
  <xsl:template match="a:entry">
    <article class="hentry">
      <xsl:attribute name="id">
        <xsl:variable name="uuid" select="a:id" />
        <xsl:value-of select="translate(substring-after($uuid,'urn:uuid:'),'-','')" />
      </xsl:attribute>
      <h2><a><xsl:attribute name="href"><xsl:value-of select="a:link/@href"/></xsl:attribute><xsl:value-of select="a:title"/></a></h2>
      
      <ul>
        <xsl:apply-templates select="a:category" />
      </ul>
      <br />
      <ul>
        <xsl:apply-templates select="a:author" />
      </ul>
      <br />
      <p><xsl:value-of select="a:updated"/></p>
      
      <div class="entry-content">
        <xsl:apply-templates select="a:content/h:div/*" />
      </div>
    </article>
  </xsl:template>
  
  <xsl:template match="a:author">
    <li><xsl:value-of select="a:name"/></li>
  </xsl:template>
  
  <xsl:template match="a:category">
    <li><xsl:value-of select="@label" /></li>
  </xsl:template>

  <xsl:template match="a:content//*">
    <xsl:element name="{local-name()}">
      <xsl:copy-of select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>