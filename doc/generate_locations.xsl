<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://docbook.org/ns/docbook" xmlns:d="http://docbook.org/ns/docbook">
 <xsl:output method="xml" indent="yes"/>
 <xsl:strip-space elements="*"/>

 <xsl:param name="location_type" select="'cluster'"/>

<xsl:template match="@* | node()">
  <xsl:copy>
    <xsl:apply-templates select="@* | node()"/>
  </xsl:copy>
 </xsl:template>

 <xsl:template match="d:option/text()">
  <xsl:value-of select="substring-before(., '--')"/>
  <xsl:text>--</xsl:text>
  <xsl:value-of select="$location_type"/>
  <xsl:text>_</xsl:text>
  <xsl:value-of select="substring-after(., '--')"/>
 </xsl:template>

 <xsl:template match="@xml:id[parent::d:synopfragment]">
  <xsl:attribute name="xml:id">
   <xsl:value-of select="$location_type"/>
   <xsl:text>-</xsl:text>
   <xsl:value-of select="."/>
  </xsl:attribute>
 </xsl:template>

</xsl:stylesheet>
