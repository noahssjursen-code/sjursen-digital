<script lang="ts">
	export let points: number[] = [];
	export let width = 600;
	export let height = 70;

	$: path = (() => {
		if (points.length < 2) return '';
		const min = Math.min(...points);
		const max = Math.max(...points);
		const span = max - min || 1;
		const pad = 6;
		return points
			.map((v, i) => {
				const x = pad + (i / (points.length - 1)) * (width - pad * 2);
				const y = height - pad - ((v - min) / span) * (height - pad * 2);
				return `${x.toFixed(1)},${y.toFixed(1)}`;
			})
			.join(' ');
	})();
	$: last = points.length ? points[points.length - 1] : null;
</script>

{#if points.length >= 2}
	<div class="spark">
		<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none">
			<polyline
				points={path}
				fill="none"
				stroke="#000"
				stroke-width="2.5"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
		</svg>
		<span class="last">{last}</span>
	</div>
{:else}
	<p class="empty">Not enough data points yet.</p>
{/if}

<style>
	.spark {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	svg {
		width: 100%;
		height: 70px;
		border: 2px solid #000;
		border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
		background: #fff;
	}
	.last {
		font-family: monospace;
		font-weight: 900;
		font-size: 1.4rem;
		min-width: 4rem;
		text-align: right;
	}
	.empty {
		margin: 0;
		opacity: 0.6;
		font-size: 0.9rem;
	}
</style>
