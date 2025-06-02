import { SvelteComponentTyped } from "svelte";
export interface SecGeminiLogoProps {
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
type SecGeminiLogoProps_ = typeof __propDef.props;
export type SecGeminiLogoEvents = typeof __propDef.events;
export type SecGeminiLogoSlots = typeof __propDef.slots;
export default class SecGeminiLogo extends SvelteComponentTyped<SecGeminiLogoProps_, SecGeminiLogoEvents, SecGeminiLogoSlots> {
}
export {};
