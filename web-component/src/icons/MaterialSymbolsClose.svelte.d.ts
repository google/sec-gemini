import { SvelteComponentTyped } from "svelte";
export interface MaterialSymbolsCloseProps {
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
type MaterialSymbolsCloseProps_ = typeof __propDef.props;
export type MaterialSymbolsCloseEvents = typeof __propDef.events;
export type MaterialSymbolsCloseSlots = typeof __propDef.slots;
export default class MaterialSymbolsClose extends SvelteComponentTyped<MaterialSymbolsCloseProps_, MaterialSymbolsCloseEvents, MaterialSymbolsCloseSlots> {
}
export {};
