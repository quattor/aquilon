package org.quattor.epub;

import java.io.Closeable;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class EpubCreator {

    private static final int BUFFER_SIZE = 1024;

    private static final String MIMETYPE = "mimetype";

    public static void main(String[] args) {

        File rootDir = new File(args[0]);

        removeEpubFiles(rootDir);
        processRootDirectories(rootDir);

    }

    public static void processRootDirectories(File rootDir) {

        if (rootDir != null && rootDir.isDirectory()) {
            for (String f : rootDir.list()) {
                File epubDir = new File(rootDir, f);
                if (epubDir.isDirectory()) {
                    createArchive(epubDir);
                }
            }

        }

    }

    // Create the ZIP archive. The mimetype must be the first file in the
    // archive and it must not be compressed.
    public static void createArchive(File epubDir) {

        String epubName = epubDir.getName() + ".epub";
        File epubPath = new File(epubDir.getParent(), epubName);

        System.out.println("epub output file: " + epubPath);

        List<File> files = collectFiles(epubDir);

        createZipArchive(epubPath, epubDir, files);

    }

    public static List<File> collectFiles(File epubDir) {
        return collectFiles(epubDir.getAbsoluteFile(), new ArrayList<File>());
    }

    public static List<File> collectFiles(File file, List<File> files) {

        if (file.isDirectory()) {
            for (String f : file.list()) {
                collectFiles(new File(file, f), files);
            }
        } else {
            if (!MIMETYPE.equals(file.getName())) {
                files.add(file);
            }
        }
        return files;
    }

    public static void removeEpubFiles(File rootDir) {
        if (rootDir != null && rootDir.isDirectory()) {
            for (String f : rootDir.list()) {
                if (f.endsWith(".epub")) {
                    File file = new File(rootDir, f);
                    if (file.delete()) {
                        System.out.println("Deleting: " + file);
                    } else {
                        System.out.println("Could not delete: " + file);
                    }
                }
            }
        }

    }

    public static void createZipArchive(File zipFilename, File epubDir,
            List<File> files) {

        FileOutputStream fos = null;
        ZipOutputStream zipstream = null;

        URI rootURI = epubDir.getAbsoluteFile().toURI();

        File mimetypeFile = new File(epubDir, MIMETYPE);

        try {

            fos = new FileOutputStream(zipFilename);
            zipstream = new ZipOutputStream(fos);

            zipstream.setLevel(ZipOutputStream.STORED);
            writeZipEntry(zipstream, mimetypeFile,
                    relativeFilename(rootURI, mimetypeFile));
            zipstream.setLevel(ZipOutputStream.DEFLATED);
            for (File file : files) {
                writeZipEntry(zipstream, file, relativeFilename(rootURI, file));
            }

        } catch (IOException consumed) {

            System.err.println("ERROR: " + consumed.getMessage());

        } finally {

            closeReliably(zipstream);
            closeReliably(fos);

        }
    }

    public static String relativeFilename(URI rootURI, File file) {
        URI fileURI = file.toURI();
        return rootURI.relativize(fileURI).toString();
    }

    public static void writeZipEntry(ZipOutputStream zipstream, File file,
            String name) {

        FileInputStream in = null;
        try {

            in = new FileInputStream(file);

            ZipEntry zipEntry = new ZipEntry(name);

            zipstream.putNextEntry(zipEntry);

            byte[] buffer = new byte[BUFFER_SIZE];

            int len;
            while ((len = in.read(buffer)) > 0) {
                zipstream.write(buffer, 0, len);
            }

            zipstream.closeEntry();

        } catch (IOException consumed) {
            System.out.println("WARNING: " + consumed.getMessage());
        } finally {
            closeReliably(in);
        }
    }

    public static void closeReliably(Closeable closeable) {
        if (closeable != null) {
            try {
                closeable.close();
            } catch (IOException consumed) {
                System.out.println("WARNING: " + consumed.getMessage());
            }
        }
    }

}
