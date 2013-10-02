# Aquilon Book

This repository contains the sources for the Aquilon book.  


# Building Documentation

The documentation sources are written in Markdown format, specifically
the [pandoc variant][pandoc-md] of Markdown.  These sources are then
converted to html, PDF, and EPUB formats.

The process to generate the documentation is controlled via
[maven][maven], so you'll need to have java and maven installed.  The
`mvn` command needs to be in your path.

You'll also need to have Python, [pandoc][pandoc], and [LaTeX][latex]
installed on your machine to generate the documentation in all of the
output formats. 

Once all of the dependencies are installed, building the documentation
can be done with:

    $ mvn clean install

The output files will then appear in the `target/version` subdirectory
where the `version` is the version in the `pom.xml` file.  All of the
documentation will be bundled into the tarball and zipfile in the
`target` subdirectory.


# License

The code in the public repositories is licensed under the Apache
license.

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.  You may
obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.


[pandoc-md]: http://johnmacfarlane.net/pandoc/README.html#pandocs-markdown
[pandoc]: http://johnmacfarlane.net/pandoc/
[latex]: http://www.latex-project.org
