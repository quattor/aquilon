<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fo="http://www.w3.org/1999/XSL/Format" 
                xmlns:db="http://docbook.org/ns/docbook"
                xmlns:dc="http://purl.org/dc/elements/1.1/"  
                xmlns:exsl="http://exslt.org/common" 
                xmlns:h="http://www.w3.org/1999/xhtml"
                xmlns:ncx="http://www.daisy.org/z3986/2005/ncx/"
                xmlns:ng="http://docbook.org/docbook-ng"
                xmlns:opf="http://www.idpf.org/2007/opf"
                xmlns:stext="http://nwalsh.com/xslt/ext/com.nwalsh.saxon.TextFactory"
                xmlns:str="http://exslt.org/strings"
                xmlns:d="http://docbook.org/ns/docbook"
                version="1.0">
  
  <xsl:import href="urn:docbkx:stylesheet" />

  <!-- Turn this off for epub, otherwise all functions are prefixed with fsfunc in the output. -->
  <xsl:param name="funcsynopsis.decoration" select="0"/>

  <xsl:template name="opf.manifest">
    <xsl:element namespace="http://www.idpf.org/2007/opf" name="manifest">
      <xsl:element namespace="http://www.idpf.org/2007/opf" name="item">
        <xsl:attribute name="id"> <xsl:value-of select="$epub.ncx.toc.id"/> </xsl:attribute>
        <xsl:attribute name="media-type">application/x-dtbncx+xml</xsl:attribute>
        <xsl:attribute name="href"><xsl:value-of select="$epub.ncx.filename"/> </xsl:attribute>
      </xsl:element>

      <xsl:if test="contains($toc.params, 'toc')">
        <xsl:element namespace="http://www.idpf.org/2007/opf" name="item">
          <xsl:attribute name="id"> <xsl:value-of select="$epub.html.toc.id"/> </xsl:attribute>
          <xsl:attribute name="media-type">application/xhtml+xml</xsl:attribute>
          <xsl:attribute name="href">
            <xsl:call-template name="toc-href">
              <xsl:with-param name="node" select="/*"/>
            </xsl:call-template>
          </xsl:attribute>
        </xsl:element>
      </xsl:if>  

      <xsl:if test="$html.stylesheet != ''">
        <xsl:element namespace="http://www.idpf.org/2007/opf" name="item">
          <xsl:attribute name="media-type">text/css</xsl:attribute>
          <xsl:attribute name="id">css</xsl:attribute>
          <xsl:attribute name="href"><xsl:value-of select="$html.stylesheet"/></xsl:attribute>
        </xsl:element>
      </xsl:if>

      <xsl:if test="/*/*[d:cover or contains(name(.), 'info')]//d:mediaobject[@role='cover' or ancestor::d:cover]"> 
        <xsl:element namespace="http://www.idpf.org/2007/opf" name="item">
          <xsl:attribute name="id"> <xsl:value-of select="$epub.cover.id"/> </xsl:attribute>
          <xsl:attribute name="href"> 
            <xsl:value-of select="$epub.cover.html"/>
          </xsl:attribute>
          <xsl:attribute name="media-type">application/xhtml+xml</xsl:attribute>
        </xsl:element>
      </xsl:if>  

      <xsl:choose>
        <xsl:when test="$epub.embedded.fonts != '' and not(contains($epub.embedded.fonts, ','))">
          <xsl:call-template name="embedded-font-item">
            <xsl:with-param name="font.file" select="$epub.embedded.fonts"/> <!-- There is just one -->
          </xsl:call-template>
        </xsl:when>
        <xsl:when test="$epub.embedded.fonts != ''">
          <xsl:variable name="font.file.tokens" select="str:tokenize($epub.embedded.fonts, ',')"/>
          <xsl:for-each select="exsl:node-set($font.file.tokens)">
            <xsl:call-template name="embedded-font-item">
              <xsl:with-param name="font.file" select="."/>
              <xsl:with-param name="font.order" select="position()"/>
            </xsl:call-template>
          </xsl:for-each>
        </xsl:when>
      </xsl:choose>

      <!-- TODO: be nice to have a id="titlepage" here -->
      <xsl:apply-templates select="//d:part|
                                   //d:book[*[last()][self::d:bookinfo]]|
                                   //d:book[d:bookinfo]|
                                   //d:book[d:info]|
                                   /d:set|
                                   /d:set/d:book|
                                   //d:reference|
                                   //d:preface|
                                   //d:chapter|
                                   //d:bibliography|
                                   //d:appendix|
                                   //d:article|
                                   //d:glossary|
                                   //d:section|
                                   //d:sect1|
                                   //d:sect2|
                                   //d:sect3|
                                   //d:sect4|
                                   //d:sect5|
                                   //d:refentry|
                                   //d:colophon|
                                   //d:bibliodiv[d:title]|
                                   //d:index|
                                   //d:setindex|
                                   //d:graphic|
                                   //d:inlinegraphic|
                                   //d:mediaobject|
                                   //d:mediaobjectco|
                                   //d:inlinemediaobject" 
                           mode="opf.manifest"/>
      <xsl:call-template name="opf.calloutlist"/>
    </xsl:element>
  </xsl:template>


  <!-- Warning: While the test indicate this match list is accurate, it may 
       need further tweaking to ensure _never_ dropping generated content (XHTML)
       from the manifest (OPF file) -->
  <xsl:template
      match="d:set|
            d:book[parent::d:set]|
            d:book[*[last()][self::d:bookinfo]]|
            d:book[d:bookinfo]|
            d:book[d:info]|
            d:article|
            d:part|
            d:reference|
            d:preface|
            d:chapter|
            d:bibliography|
            d:appendix|
            d:glossary|
            d:section|
            d:sect1|
            d:sect2|
            d:sect3|
            d:sect4|
            d:sect5|
            d:refentry|
            d:colophon|
            d:bibliodiv[d:title]|
            d:setindex|
            d:index"
      mode="opf.manifest">
    <xsl:variable name="href">
      <xsl:call-template name="href.target.with.base.dir">
        <xsl:with-param name="context" select="/" />
        <!-- Generate links relative to the location of root file/toc.xml file -->
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="id">
      <xsl:value-of select="generate-id(.)"/>
    </xsl:variable>

    <xsl:variable name="is.chunk">
      <xsl:call-template name="chunk">
        <xsl:with-param name="node" select="."/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:if test="$is.chunk != 0">
      <xsl:element namespace="http://www.idpf.org/2007/opf" name="item">
        <xsl:attribute name="id"> <xsl:value-of select="$id"/> </xsl:attribute>
        <xsl:attribute name="href"> <xsl:value-of select="$href"/> </xsl:attribute>
        <xsl:attribute name="media-type">application/xhtml+xml</xsl:attribute>
      </xsl:element>
    </xsl:if>  
  </xsl:template>  

</xsl:stylesheet>
