import { SvelteComponentTyped } from "svelte";
export interface MdiIncognitoProps {
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
type MdiIncognitoProps_ = typeof __propDef.props;
export type MdiIncognitoEvents = typeof __propDef.events;
export type MdiIncognitoSlots = typeof __propDef.slots;
export default class MdiIncognito extends SvelteComponentTyped<MdiIncognitoProps_, MdiIncognitoEvents, MdiIncognitoSlots> {
}
export {};
