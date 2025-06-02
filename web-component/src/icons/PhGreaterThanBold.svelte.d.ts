import { SvelteComponentTyped } from "svelte";
export interface PhGreaterThanBoldProps {
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
type PhGreaterThanBoldProps_ = typeof __propDef.props;
export type PhGreaterThanBoldEvents = typeof __propDef.events;
export type PhGreaterThanBoldSlots = typeof __propDef.slots;
export default class PhGreaterThanBold extends SvelteComponentTyped<PhGreaterThanBoldProps_, PhGreaterThanBoldEvents, PhGreaterThanBoldSlots> {
}
export {};
