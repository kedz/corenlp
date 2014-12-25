import java.io.*;
import java.net.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.Properties;
import edu.stanford.nlp.pipeline.*;
import java.util.LinkedList; 

class CoreNlpServer {

    static volatile boolean shutdownFlag = false;
    static volatile LinkedList<PrintWriter> closingClientPrintWriters = new LinkedList<PrintWriter>();
    static volatile LinkedList<BufferedReader> closingClientBufferedReaders = new LinkedList<BufferedReader>();
    static volatile ServerSocket serverSocket = null;

    static String helpMessage =
      "usage: CoreNlpServer [-p PORT_NUM] [-t THREADS] [-a ANN1,ANN2...] [-h]";

    public static void main(String args[]) throws IOException, InterruptedException {
        int portNum = 8090;
        int numArgs = args.length;
        int numThreads = 1;

        String[] annotators =
            {"tokenize", "ssplit", "pos", "lemma", "ner", "parse", "dcoref"};

        /* Parse args */
        for (int i = 0; i < numArgs; i++) {
            if (args[i].equals("-h") || args[i].equals("--help")) {
                System.out.println(helpMessage);
                System.exit(0);
            } else if (args[i].equals("-p") && (i + 1) < numArgs) {
                portNum = Integer.parseInt(args[i+1]);
                i++;
            } else if (args[i].equals("-t") && (i + 1) < numArgs) {
                numThreads = Integer.parseInt(args[i+1]);
                i++;
            } else if (args[i].equals("-a") && (i + 1) < numArgs) {
                annotators = args[i+1].split(",");
            }
        }

        System.out.println("Loading CoreNLP models...");

        String annString = annotators[0];
        for (int i = 1; i < annotators.length; i++)
            annString += ", " + annotators[i];
        Properties props = new Properties();
        props.put("annotators", annString);
        props.put("parse.maxlen", 40);
        props.put("pos.maxlen", 40);
        props.put("ner.maxlen", 40);
        props.put("ssplit.newlineIsSentenceBreak", "two");
        StanfordCoreNLP pipeline = new StanfordCoreNLP(props);
        ExecutorService threadPool = Executors.newFixedThreadPool(numThreads);

        System.out.println("Starting server on port " + portNum
            + " with " + numThreads + " threads...");

        serverSocket = new ServerSocket(portNum);
        Socket clientSocket = null;

       
        while (shutdownFlag == false) {
            try {
                clientSocket = serverSocket.accept();
                threadPool.execute(new CoreNlpHandler(clientSocket, pipeline));
            } catch (IOException e) {
                System.out.println("Attempting to shutdown CoreNlpServer...");
            }
        }

        threadPool.shutdown();
        threadPool.awaitTermination(9999L, TimeUnit.SECONDS);

        for (int i = 0; i < closingClientPrintWriters.size(); i++) {
            PrintWriter pw = closingClientPrintWriters.get(i);
            pw.write(CoreNlpHandler.SUCCESS);
            pw.flush();
            pw.close();
       }
 
       for (int i = 0; i < closingClientBufferedReaders.size(); i++) {
            BufferedReader br = closingClientBufferedReaders.get(i);
            br.close();
       }
    }
}
                      
