import com.txanalyzer.bot.*;
public class BotCoreTest {
    static BotCore.Observation obs(double confidence,double health,double danger,boolean enemy,boolean minions,long t){
        return new BotCore.Observation(BotCore.Phase.MATCH,confidence,health,0.8,danger,0.95,true,false,false,minions,enemy,false,false,true,t);
    }
    static void expect(BotCore.Action want,BotCore.Decision got){if(got.action!=want)throw new AssertionError(want+" != "+got);}
    public static void main(String[] args){
        BotCore core=new BotCore();
        expect(BotCore.Action.RETREAT,core.decide(obs(.99,.20,.1,true,true,1000),1100));
        expect(BotCore.Action.FIGHT,core.decide(obs(.99,.90,.1,true,true,1000),1100));
        expect(BotCore.Action.FARM,core.decide(obs(.99,.90,.1,false,true,1000),1100));
        expect(BotCore.Action.WAIT,core.decide(obs(.3,.90,.1,true,true,1000),1100));
        expect(BotCore.Action.WAIT,core.decide(obs(.99,.90,.1,true,true,1000),2001));
        BotSession session=new BotSession();
        expect(BotCore.Action.STOP,session.evaluate(obs(.99,.90,.1,true,true,1000),1100));
        System.out.println("PASS: 6 bot-core tests");
    }
}
