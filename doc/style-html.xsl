<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <!--- XXX Pass this from the command line -->
  <xsl:import href="/ms/dist/fsf/PROJ/docbook-xsl-ns/1.77.1/common/xhtml/chunk.xsl"/>
  <xsl:param name="refentry.generate.name">0</xsl:param>
  <xsl:param name="refentry.generate.title">1</xsl:param>
  <xsl:param name="variablelist.as.table">0</xsl:param>
  <xsl:param name="html.stylesheet">style.css</xsl:param>
  <xsl:param name="admon.graphics">1</xsl:param>
  <xsl:param name="admon.graphics.path">images/</xsl:param>
  <xsl:param name="admon.graphics.extension">.png</xsl:param>
  <xsl:param name="root.filename"></xsl:param>
  <xsl:param name="generate.manifest">0</xsl:param>
  <xsl:param name="use.id.as.filename">1</xsl:param>
  <xsl:param name="chunker.output.indent">yes</xsl:param>
  <xsl:param name="index.on.type">1</xsl:param>
  <xsl:param name="base.dir">html/</xsl:param>
</xsl:stylesheet>
