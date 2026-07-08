<script lang="ts">
	export let state: string = 'ok';
</script>

<span class="state state-{state}">{state}</span>

<style>
	.state {
		display: inline-block;
		font-weight: 800;
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border: 2px solid #000;
		border-radius: 6px 12px 6px 12px/12px 6px 12px 6px;
		background: #fff;
		color: #000;
	}
	.state-ok {
		background: #fff;
	}
	.state-suspect {
		background: #000;
		color: #fff;
		opacity: 0.6;
	}
	.state-alarm,
	.state-active {
		background: #000;
		color: #fff;
	}
	.state-silent {
		background: repeating-linear-gradient(45deg, #000, #000 4px, #fff 4px, #fff 8px);
		color: #fff;
		text-shadow:
			1px 1px 0 #000,
			-1px -1px 0 #000,
			1px -1px 0 #000,
			-1px 1px 0 #000;
	}
	.state-resolved,
	.state-acknowledged {
		border-style: dashed;
		opacity: 0.6;
	}
</style>
