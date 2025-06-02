import { SvelteComponentTyped } from "svelte";
export interface MaterialSymbolsBoltProps {
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
type MaterialSymbolsBoltProps_ = typeof __propDef.props;
export type MaterialSymbolsBoltEvents = typeof __propDef.events;
export type MaterialSymbolsBoltSlots = typeof __propDef.slots;
export default class MaterialSymbolsBolt extends SvelteComponentTyped<MaterialSymbolsBoltProps_, MaterialSymbolsBoltEvents, MaterialSymbolsBoltSlots> {
}
export {};
