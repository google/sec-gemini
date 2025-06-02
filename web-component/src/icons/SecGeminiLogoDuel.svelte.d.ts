import { SvelteComponentTyped } from "svelte";
export interface SecGeminiLogoProps {
    size?: number;
    class?: string;
    animate?: boolean;
    incognito?: boolean;
}
declare const __propDef: {
    props: Record<string, never>;
    events: {
        [evt: string]: CustomEvent<any>;
    };
    slots: {};
};
export type SecGeminiLogoDuelProps = typeof __propDef.props;
export type SecGeminiLogoDuelEvents = typeof __propDef.events;
export type SecGeminiLogoDuelSlots = typeof __propDef.slots;
export default class SecGeminiLogoDuel extends SvelteComponentTyped<SecGeminiLogoDuelProps, SecGeminiLogoDuelEvents, SecGeminiLogoDuelSlots> {
}
export {};
