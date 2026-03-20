<script lang="ts">
  export interface SecGeminiLogoProps {
    size?: number;
    class?: string;
    animate?: boolean;
    incognito?: boolean;
  }
  const {
    size = 0.7,
    class: className = "",
    animate = false,
    incognito = false,
  }: SecGeminiLogoProps = $props();
  const purpleGradientStops = [
    { offset: "0", stopColor: "#8A2BE2" },
    { offset: ".27", stopColor: "#9370DB" },
    { offset: ".78", stopColor: "#BA55D3" },
    { offset: "1", stopColor: "#C71585" },
  ];
  const originalGradientStops = [
    { offset: "0", stopColor: "#217bfe" },
    { offset: ".27", stopColor: "#078efb" },
    { offset: ".78", stopColor: "#a190ff" },
    { offset: "1", stopColor: "#bd99fe" },
  ];
  let currentGradientStops = incognito
    ? purpleGradientStops
    : originalGradientStops;
</script>

<svg
  class={className}
  width={`${size}em`}
  height={`${size}em`}
  xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 101.3 127.07"
>
  <defs>
    <linearGradient
      id="shieldGradient"
      x1="14.24"
      y1="63.53"
      x2="87.06"
      y2="63.53"
      gradientUnits="userSpaceOnUse"
    >
      {#each currentGradientStops as stop}
        <stop offset={stop.offset} stop-color={stop.stopColor} />
      {/each}
    </linearGradient>
    <linearGradient
      id="shieldPathGradient"
      x1=".25"
      x2="101.05"
      href="#shieldGradient"
    />
    <linearGradient
      id="shieldStrokeGradient"
      x1="0"
      y1="63.53"
      x2="101.3"
      y2="63.53"
      href="#shieldGradient"
    />
  </defs>
  <g id="Layer_1-2" data-name="Layer 1">
    <g id="standard-transparent">
      <g id="logo">
        <path
          id="sparkle"
          class={`${animate ? "origin-center animate-sparkle-sequence opacity-0" : ""} `}
          style="stroke-dasharray: 800;"
          fill="url(#shieldPathGradient)"
          stroke="url(#shieldStrokeGradient)"
          stroke-miterlimit="10"
          d="M86.91,63.4c-4.98,0-9.6-.95-13.98-2.8-4.38-1.94-8.26-4.56-11.51-7.81-3.25-3.25-5.87-7.13-7.81-11.51-1.88-4.38-2.8-9.01-2.8-13.98,0-.09-.06-.15-.15-.15s-.15.06-.15.15c0,4.98-.98,9.6-2.89,13.98-1.88,4.38-4.47,8.26-7.69,11.51-3.25,3.25-7.13,5.87-11.51,7.81-4.38,1.88-9.01,2.8-14.01,2.8-.09,0-.15.06-.15.15s.06.15.15.15c4.98,0,9.6.98,14.01,2.89,4.38,1.88,8.26,4.47,11.51,7.69,3.25,3.25,5.84,7.13,7.69,11.51,1.94,4.38,2.89,9.01,2.89,13.98,0,.09.06.15.15.15s.15-.06.15-.15c0-4.98.95-9.6,2.8-13.98,1.94-4.38,4.56-8.26,7.81-11.51,3.25-3.25,7.13-5.84,11.51-7.69,4.38-1.94,9.01-2.89,13.98-2.89.09,0,.15-.06.15-.15s-.06-.15-.15-.15Z"
        />
        <path
          id="shield"
          class={`${animate ? "animate-draw-shield fill-opacity-0 origin-center stroke-[1.5px]" : ""} `}
          fill="url(#shieldGradient)"
          d="M50.65,126.82h-.02c-1.24-.02-2.47-.31-3.66-.87-1.91-.9-3.83-2.18-5.53-3.32l-.45-.3c-2.03-1.35-4.05-2.77-6-4.14-.5-.35-1-.7-1.5-1.05-4.13-2.88-8.4-5.86-12.08-9.45-3.77-3.69-7.18-7.96-10.13-12.68-2.1-3.37-3.94-6.95-5.48-10.64C2.17,75.68.25,66.1.25,56.67v-29.77c0-5.44,3.43-10.33,8.55-12.17L47.15.86c1.12-.41,2.3-.61,3.5-.61s2.37.21,3.5.61l38.36,13.86c5.11,1.85,8.55,6.74,8.55,12.17v29.77c0,9.43-1.92,19.01-5.54,27.7-1.54,3.69-3.38,7.27-5.48,10.64-2.95,4.73-6.35,8.99-10.13,12.68-3.68,3.6-7.95,6.58-12.08,9.46-.5.35-1,.7-1.5,1.05-1.96,1.37-3.98,2.79-6.01,4.14l-.45.3c-1.7,1.13-3.62,2.42-5.53,3.32-1.19.56-2.42.85-3.66.87h-.02ZM50.65,3.58c-.81,0-1.61.14-2.37.41L9.93,17.85c-3.8,1.37-6.35,5.01-6.35,9.05v29.77c0,8.99,1.83,18.13,5.29,26.42,1.47,3.52,3.23,6.94,5.24,10.16,2.81,4.5,6.05,8.56,9.63,12.06,3.49,3.4,7.64,6.3,11.66,9.11.5.35,1,.7,1.5,1.05,1.94,1.36,3.95,2.77,5.94,4.09l.45.3c1.68,1.12,3.41,2.28,5.1,3.07.76.36,1.5.54,2.26.55.76-.01,1.5-.19,2.26-.55,1.68-.79,3.42-1.95,5.1-3.07l.45-.3c2-1.33,4-2.73,5.93-4.09.51-.36,1.01-.71,1.51-1.06,4.02-2.8,8.17-5.7,11.66-9.11,3.58-3.5,6.82-7.56,9.63-12.06,2-3.22,3.77-6.63,5.24-10.16,3.46-8.29,5.29-17.43,5.29-26.42v-29.77c0-4.04-2.55-7.67-6.35-9.05L53.02,3.99c-.76-.27-1.56-.41-2.37-.41Z"
        />
      </g>
    </g>
  </g>
</svg>
