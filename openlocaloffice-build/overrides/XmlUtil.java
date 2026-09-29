package com.openlocal.office.core;

import java.io.*;
import java.nio.charset.StandardCharsets;
import javax.xml.XMLConstants;
import javax.xml.parsers.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.*;
import org.xml.sax.InputSource;

final class XmlUtil {
  private XmlUtil() {}

  static Document parse(byte[] bytes) throws Exception {
    DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
    f.setNamespaceAware(true);
    try { f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true); } catch (Exception ignored) {}
    try { f.setFeature("http://xml.org/sax/features/external-general-entities", false); } catch (Exception ignored) {}
    try { f.setFeature("http://xml.org/sax/features/external-parameter-entities", false); } catch (Exception ignored) {}
    try { f.setAttribute("http://javax.xml.XMLConstants/property/accessExternalDTD", ""); } catch (Exception ignored) {}
    try { f.setAttribute("http://javax.xml.XMLConstants/property/accessExternalSchema", ""); } catch (Exception ignored) {}
    DocumentBuilder b = f.newDocumentBuilder();
    try (ByteArrayInputStream in = new ByteArrayInputStream(bytes)) { return b.parse(in); }
  }

  static byte[] bytes(Document doc) throws Exception {
    TransformerFactory tf = TransformerFactory.newInstance();
    try { tf.setAttribute("http://javax.xml.XMLConstants/property/accessExternalDTD", ""); } catch (Exception ignored) {}
    try { tf.setAttribute("http://javax.xml.XMLConstants/property/accessExternalStylesheet", ""); } catch (Exception ignored) {}
    Transformer t = tf.newTransformer();
    t.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
    t.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "no");
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    t.transform(new DOMSource(doc), new StreamResult(out));
    return out.toByteArray();
  }

  static Element firstChild(Element parent, String local) {
    for (Node n = parent.getFirstChild(); n != null; n = n.getNextSibling()) {
      if (n instanceof Element && local.equals(n.getLocalName())) return (Element)n;
    }
    return null;
  }

  static String text(Element parent, String local) {
    Element e = firstChild(parent, local); return e == null ? null : e.getTextContent();
  }

  static void removeChildrenByLocal(Element parent, String local) {
    for (Node n = parent.getFirstChild(); n != null;) {
      Node next = n.getNextSibling();
      if (n instanceof Element && local.equals(n.getLocalName())) parent.removeChild(n);
      n = next;
    }
  }
}
