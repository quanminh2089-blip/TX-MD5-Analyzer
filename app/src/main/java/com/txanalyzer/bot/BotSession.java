package com.txanalyzer.bot;
/** Safety gate: never dispatch input automatically from this module. */
public final class BotSession {
    private final BotCore core = new BotCore();
    private boolean enabled = false;
    public void setEnabled(boolean enabled){this.enabled=enabled;}
    public boolean isEnabled(){return enabled;}
    public BotCore.Decision evaluate(BotCore.Observation frame,long nowMs){
        if(!enabled) return new BotCore.Decision(BotCore.Action.STOP,"Bot disabled");
        return core.decide(frame,nowMs);
    }
}
