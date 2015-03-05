package edu.columbia.cs.nlp;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import java.net.InetAddress;
import java.util.Date;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import edu.stanford.nlp.pipeline.*;
import java.io.*;

@Sharable
public class CoreNLPServerHandler 
  extends SimpleChannelInboundHandler<String> {
   
    public boolean verbose;
    private StanfordCoreNLP pipeline;

    public static final char EOF = '\u0000'; 
    public static final String ANNOTATE = "<CNLPANNOTATE>";
    public static final String SHUTDOWN = "<CNLPSHUTDOWN>";
    public static final String STATUS = "<CNLPSTATUS>";

    public CoreNLPServerHandler(StanfordCoreNLP pipeline) {
        this.pipeline = pipeline;
        this.verbose = true;
    }

    @Override
    public void channelActive(ChannelHandlerContext ctx) throws Exception {
    }

    @Override
    public void channelRead0(ChannelHandlerContext ctx, String request) 
      throws Exception {
        
        if (request.startsWith(ANNOTATE)) {
            String text = request.substring(ANNOTATE.length());
            if (verbose) System.out.println(
                "annotating text of length " + text.length());
            String xmlString = annotateText(text);
            ctx.writeAndFlush(xmlString+EOF);

        } else if (request.startsWith(SHUTDOWN)) {
            if (verbose) System.out.println("shutting down!");
            ctx.channel().close();
            ctx.channel().parent().close();
        }        
    }

    public String annotateText(String text) {
        Annotation document = new Annotation(text);
        pipeline.annotate(document);
        ByteArrayOutputStream os = new ByteArrayOutputStream();

        try {
            Class<?> clazz = 
                Class.forName("edu.stanford.nlp.pipeline.XMLOutputter");
            Method method = 
                clazz.getMethod("xmlPrint", Annotation.class,
                                OutputStream.class, StanfordCoreNLP.class);
            method.invoke(null, document, os, pipeline);
            
        } catch (NoSuchMethodException e) {
          throw new RuntimeException(e);
        } catch (IllegalAccessException e) {
          throw new RuntimeException(e);
        } catch (ClassNotFoundException e) {
          throw new RuntimeException(e);
        } catch (InvocationTargetException e) {
          throw new RuntimeException(e);
        }
        return os.toString();   
    }

@Override
public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
cause.printStackTrace();
ctx.close();
}
}
