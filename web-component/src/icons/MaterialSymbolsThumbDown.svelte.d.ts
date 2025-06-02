import { SvelteComponentTyped } from "svelte";
export interface MaterialSymbolsThumbDownProps {
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
type MaterialSymbolsThumbDownProps_ = typeof __propDef.props;
export type MaterialSymbolsThumbDownEvents = typeof __propDef.events;
export type MaterialSymbolsThumbDownSlots = typeof __propDef.slots;
export default class MaterialSymbolsThumbDown extends SvelteComponentTyped<MaterialSymbolsThumbDownProps_, MaterialSymbolsThumbDownEvents, MaterialSymbolsThumbDownSlots> {
}
export {};
