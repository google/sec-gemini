import { SvelteComponentTyped } from "svelte";
export interface RiMoonLineProps {
    size?: number;
    class?: string;
}
declare const __propDef: {
    props: Record<string, never>;
    events: {
        [evt: string]: CustomEvent<any>;
    };
    slots: {};
};
export type SparkleProps = typeof __propDef.props;
export type SparkleEvents = typeof __propDef.events;
export type SparkleSlots = typeof __propDef.slots;
export default class Sparkle extends SvelteComponentTyped<SparkleProps, SparkleEvents, SparkleSlots> {
}
export {};
