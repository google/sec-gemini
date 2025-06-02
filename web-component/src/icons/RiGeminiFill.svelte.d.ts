import { SvelteComponentTyped } from "svelte";
export interface RiGeminiFillProps {
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
type RiGeminiFillProps_ = typeof __propDef.props;
export type RiGeminiFillEvents = typeof __propDef.events;
export type RiGeminiFillSlots = typeof __propDef.slots;
export default class RiGeminiFill extends SvelteComponentTyped<RiGeminiFillProps_, RiGeminiFillEvents, RiGeminiFillSlots> {
}
export {};
