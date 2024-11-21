<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    viewBox="0 0 200 200"
  >
    <!-- Background circle -->
    <circle
      cx="100"
      cy="100"
      r="90"
      fill="#f8f9fa"
      stroke="#2a4858"
      stroke-width="2"
    />

    <!-- Network nodes and connections -->
    <g id="network">
      <!-- Connections -->
      <line
        x1="70"
        y1="70"
        x2="130"
        y2="90"
        stroke="#486878"
        stroke-width="1.5"
      />
      <line
        x1="70"
        y1="70"
        x2="90"
        y2="130"
        stroke="#486878"
        stroke-width="1.5"
      />
      <line
        x1="130"
        y1="90"
        x2="90"
        y2="130"
        stroke="#486878"
        stroke-width="1.5"
      />
      <line
        x1="130"
        y1="90"
        x2="150"
        y2="60"
        stroke="#486878"
        stroke-width="1.5"
      />
      <line
        x1="90"
        y1="130"
        x2="140"
        y2="140"
        stroke="#486878"
        stroke-width="1.5"
      />

      <!-- Nodes as squares with play buttons -->
      <!-- Large node -->
      <rect x="58" y="58" width="24" height="24" fill="#2a4858" rx="2" />
      <path d="M65 65 L65 75 L75 70 Z" fill="white" />

      <!-- Medium node -->
      <rect x="122" y="82" width="16" height="16" fill="#486878" rx="2" />
      <path d="M127 87 L127 93 L133 90 Z" fill="white" />

      <!-- Medium-large node -->
      <rect x="80" y="120" width="20" height="20" fill="#486878" rx="2" />
      <path d="M86 126 L86 134 L94 130 Z" fill="white" />

      <!-- Small node -->
      <rect x="144" y="54" width="12" height="12" fill="#6d8fa0" rx="2" />
      <path d="M148 58 L148 62 L152 60 Z" fill="white" />

      <!-- Medium-small node -->
      <rect x="133" y="133" width="14" height="14" fill="#6d8fa0" rx="2" />
      <path d="M138 137 L138 143 L144 140 Z" fill="white" />
    </g>

    <!-- Central node -->
    <rect x="90" y="90" width="20" height="20" fill="#486878" rx="2" />
    <path d="M96 96 L96 104 L104 100 Z" fill="white" />
  </svg>
</template>

<script>
export default {
  name: 'FilonovLogo',
  props: {
    size: {
      type: [Number, String],
      default: 200,
    },
  },
};
</script>
