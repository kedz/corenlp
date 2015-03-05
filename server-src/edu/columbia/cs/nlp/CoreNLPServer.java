package edu.columbia.cs.nlp;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;
import java.util.Properties;
import edu.stanford.nlp.pipeline.*;

public final class CoreNLPServer {
    static final String helpMessage =
      "usage: CoreNlpServer [-p PORT_NUM] [-t THREADS] [-a ANN1,ANN2...] [-h]";

    public static void main(String[] args) throws Exception {

        int portNum = 9989;
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
        System.out.println("Starting server on port " + portNum
            + " with " + numThreads + " threads...");

        EventLoopGroup bossGroup = new NioEventLoopGroup(1);
        EventLoopGroup workerGroup = new NioEventLoopGroup(numThreads);
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .handler(new LoggingHandler(LogLevel.INFO))
                .childHandler(new CoreNLPServerInitializer(pipeline));
            b.bind(portNum).sync().channel().closeFuture().sync();
        } finally {
            bossGroup.shutdownGracefully();
            workerGroup.shutdownGracefully();
        }
    }
}
