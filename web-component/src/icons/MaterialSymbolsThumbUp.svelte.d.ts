import { SvelteComponentTyped } from "svelte";
export interface MaterialSymbolsThumbUpProps {
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
type MaterialSymbolsThumbUpProps_ = typeof __propDef.props;
export type MaterialSymbolsThumbUpEvents = typeof __propDef.events;
export type MaterialSymbolsThumbUpSlots = typeof __propDef.slots;
export default class MaterialSymbolsThumbUp extends SvelteComponentTyped<MaterialSymbolsThumbUpProps_, MaterialSymbolsThumbUpEvents, MaterialSymbolsThumbUpSlots> {
}
export {};
