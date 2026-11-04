package com.txanalyzer.bot;

/** Deterministic policy engine. No screen access, taps, or game hooks. */
public final class BotCore {
    public enum Phase { UNKNOWN, LOADING, MATCH, RESULT }
    public enum Action { WAIT, STOP, RETREAT, DEFEND, FARM, PUSH, FIGHT, BUY, RETURN_TO_LANE }
    public static final class Observation {
        public final Phase phase;
        public final double confidence, health, mana, danger, enemyConfidence;
        public final boolean alive, shopAvailable, affordableUpgrade, minionsVisible,
                enemyVisible, towerThreat, alliedWaveNearby, laneKnown;
        public final long capturedAtMs;
        public Observation(Phase phase, double confidence, double health, double mana,
                double danger, double enemyConfidence, boolean alive, boolean shopAvailable,
                boolean affordableUpgrade, boolean minionsVisible, boolean enemyVisible,
                boolean towerThreat, boolean alliedWaveNearby, boolean laneKnown,
                long capturedAtMs) {
            this.phase=phase; this.confidence=confidence; this.health=health; this.mana=mana;
            this.danger=danger; this.enemyConfidence=enemyConfidence; this.alive=alive;
            this.shopAvailable=shopAvailable; this.affordableUpgrade=affordableUpgrade;
            this.minionsVisible=minionsVisible; this.enemyVisible=enemyVisible;
            this.towerThreat=towerThreat; this.alliedWaveNearby=alliedWaveNearby;
            this.laneKnown=laneKnown; this.capturedAtMs=capturedAtMs;
        }
    }
    public static final class Decision {
        public final Action action;
        public final String reason;
        public Decision(Action action,String reason){this.action=action;this.reason=reason;}
        @Override public String toString(){return action+": "+reason;}
    }
    private final long maxFrameAgeMs;
    public BotCore(){this(900);}
    public BotCore(long maxFrameAgeMs){this.maxFrameAgeMs=maxFrameAgeMs;}
    public Decision decide(Observation o,long nowMs){
        if(o==null || o.phase==null) return new Decision(Action.WAIT,"No observation");
        if(o.phase==Phase.RESULT) return new Decision(Action.STOP,"Match finished");
        if(o.phase!=Phase.MATCH) return new Decision(Action.WAIT,"Not in match");
        if(o.capturedAtMs>nowMs || nowMs-o.capturedAtMs>maxFrameAgeMs)
            return new Decision(Action.WAIT,"Stale frame");
        if(!valid(o.confidence)||o.confidence<0.85 || !valid(o.health)||!valid(o.mana)
                || !valid(o.danger)||!valid(o.enemyConfidence))
            return new Decision(Action.WAIT,"Unreliable perception");
        if(!o.alive) return new Decision(Action.WAIT,"Waiting for respawn");
        if(o.health<0.25 || o.danger>0.82 || o.towerThreat)
            return new Decision(Action.RETREAT,"Survival priority");
        if(o.shopAvailable && o.affordableUpgrade)
            return new Decision(Action.BUY,"Upgrade available");
        if(o.enemyVisible && o.enemyConfidence>=0.90 && o.health>=0.60 && o.danger<0.40)
            return new Decision(Action.FIGHT,"Visible low-risk enemy");
        if(o.minionsVisible) return new Decision(Action.FARM,"Farm visible wave");
        if(o.alliedWaveNearby && o.health>=0.65 && o.danger<0.35)
            return new Decision(Action.PUSH,"Push with allied wave");
        if(o.laneKnown) return new Decision(Action.RETURN_TO_LANE,"Known lane");
        return new Decision(Action.WAIT,"No safe action");
    }
    private static boolean valid(double v){return !Double.isNaN(v)&&v>=0&&v<=1;}
}
