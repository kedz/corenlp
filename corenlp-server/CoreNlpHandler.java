import java.io.*;
import java.net.Socket;
import java.nio.charset.Charset;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import edu.stanford.nlp.pipeline.*;


public class CoreNlpHandler implements Runnable {

    public static char CHECK_IN = 'c'; 
    public static char ANNOTATE = 'a'; 
    public static int BUFFER_SIZE = 1024;
    public static char[] SUCCESS = "SUCCESS".toCharArray();
    protected Socket clientSocket = null;
    protected StanfordCoreNLP pipeline = null;

    public CoreNlpHandler(Socket clientSocket, StanfordCoreNLP pipeline) {
        this.clientSocket = clientSocket;
        this.pipeline = pipeline;
    }

    public void run() {
        String inputText = null;
        try {
            BufferedReader in = new BufferedReader(
                new InputStreamReader(clientSocket.getInputStream()));
            PrintWriter out = 
                new PrintWriter(clientSocket.getOutputStream(), true);

            char[] cbuf = new char[BUFFER_SIZE]; 
            int bytesRead = in.read(cbuf, 0, BUFFER_SIZE);
            int totalBytesRead = bytesRead;
             
            if (cbuf[0] == CHECK_IN) {
                out.write(SUCCESS);
                out.flush();
                out.close();
                in.close();
            } else if (cbuf[0] == ANNOTATE) {
                int messageSize = 0;
                for (int i = 1; i < bytesRead; i++) {
                    if (cbuf[i] == ' ') {
                        messageSize = charArrayToInt(cbuf, 1, i);
                        inputText = new String(
                            cbuf, i+1, bytesRead - (i+1));
                        break;       
                    }
                }

                while ((bytesRead = in.read(cbuf, 0, BUFFER_SIZE)) != -1) {
                    totalBytesRead += bytesRead;
                    inputText +=  new String(cbuf, 0, bytesRead);
                }

                String outputString = annotateString(inputText);
                messageSize = outputString.getBytes().length;
                out.write(messageSize + " " + outputString);
                out.flush();
                
            }

        } catch (IOException e) {
            System.out.println(
                "Exception caught when trying to listen on port " 
                + "or listening for a connection.");
            System.out.println(e.getMessage());
        }
    }

    public String annotateString(String inputString) {
        Annotation document = new Annotation(inputString);
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

    int charArrayToInt(char []data,int start,int end) 
        throws NumberFormatException
    {

        int result = 0;
        for (int i = start; i < end; i++) {
            int digit = (int)data[i] - (int)'0';
            if ((digit < 0) || (digit > 9)) throw new NumberFormatException();
                result *= 10;
                result += digit;
            }
        return result;
    }

}
