<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:import href="http://docbook.sourceforge.net/release/xsl-ns/current/manpages/docbook.xsl"/>
  <xsl:param name="man.output.manifest.enabled" select="0"/>
  <xsl:param name="man.output.in.separate.dir" select="1"/>
  <xsl:param name="man.output.base.dir">man/</xsl:param>
  <xsl:param name="man.output.subdirs.enabled" select="1"/>
</xsl:stylesheet>
