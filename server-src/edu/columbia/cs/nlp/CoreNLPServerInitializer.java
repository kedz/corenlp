package edu.columbia.cs.nlp;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.socket.SocketChannel;
import io.netty.handler.codec.DelimiterBasedFrameDecoder;
import io.netty.handler.codec.Delimiters;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;
import edu.stanford.nlp.pipeline.*;

public class CoreNLPServerInitializer 
  extends ChannelInitializer<SocketChannel> {

    private static final StringDecoder DECODER = new StringDecoder();
    private static final StringEncoder ENCODER = new StringEncoder();
    private static CoreNLPServerHandler SERVER_HANDLER;  
    private int maxMessageLength;
    

    public CoreNLPServerInitializer(
        StanfordCoreNLP pipeline, int maxMessageLength) {
        
        this.maxMessageLength = maxMessageLength;
        SERVER_HANDLER = new CoreNLPServerHandler(pipeline);
    }
    
    @Override
    public void initChannel(SocketChannel ch) throws Exception {
        ChannelPipeline pipeline = ch.pipeline();
        pipeline.addLast(
            new DelimiterBasedFrameDecoder(
                maxMessageLength, Delimiters.nulDelimiter()));
        // the encoder and decoder are static as these are sharable
        pipeline.addLast(DECODER);
        pipeline.addLast(ENCODER);
        // and then business logic.
        pipeline.addLast(SERVER_HANDLER);
    }
}
