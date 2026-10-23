"""Narration for sec_explainer.py (Self-Evolving Curriculum, arXiv 2505.14970), one line per beat.

Spoken form, not screen form. [Brackets] mark the words each animation of ManimGX's `say` plays on; they are not
spoken. Generate the clips with `python scripts/make_narration.py examples/sec/narration.py` (brackets are stripped there too).
"""

VOICE = "US male"

LINES = {
    # intro
    "in1": "This video gets you ready for the paper [Self-Evolving Curriculum for L L M Reasoning], by [Chen and colleagues, from Mila and ServiceNow].",
    "in2": "The idea fits in one sentence. While you train a language model with reinforcement learning, [let a small bandit algorithm decide which kind of problem to train on next]. We'll build every piece of math you need, [one piece at a time].",
    # 1. why order matters
    "cu1": "Start with the setting. In reinforcement learning with verifiable rewards, every training step takes [a batch of problems], lets the model attempt each one [several times], and checks the answers automatically. A correct answer gets [a reward of one], a wrong one gets zero.",
    "cu2": "The curriculum is the choice of [which problems go into each batch]. The paper's first figure shows that this matters a lot. Training from hard to easy, [a reverse curriculum], barely learns. [A random mix] does much better.",
    "cu3": "Why? If a problem is too easy, [all eight attempts are correct]. If it's too hard, [all eight are wrong]. Either way, every attempt looks the same, and there's nothing to learn by comparing them. The useful problems are [the ones the model solves only sometimes].",
    "cu4": "Existing fixes either [hand-design a schedule], which needs human heuristics, or [filter problems online by generating extra attempts], which is expensive. This paper [learns the schedule during training, almost for free].",
    # 2. bandits
    "mb1": "To do that, it uses [a multi-armed bandit]. The name comes from slot machines, which used to be called [one-armed bandits]. Picture [a row of machines]. Each one pays out a different amount on average, but [you don't know those averages].",
    "mb2": "Each round, [you pull one arm], and [see what it pays]. Your goal is to collect as much as possible over many rounds. So you keep [a running estimate for each arm]. We'll call it [Q].",
    "mb3": "Here's the dilemma. If you always pull the arm with the best estimate, [you exploit what you know], but you may never discover that another arm is better. If you try other arms, [you explore], but you spend pulls on worse machines. Every bandit algorithm is [a way to balance exploration and exploitation].",
    "mb4": "One more twist. In this paper, [the machines change over time]. A difficulty level that pays well today may pay little tomorrow, because the model got better at it. This is called [a non-stationary bandit], and it means [old observations should be forgotten].",
    "mb5": "And how is this different from full reinforcement learning? A bandit [has no state]. You pick an arm, you get a reward, and in the textbook version, your choice doesn't change the machines. Here it does, a little, because training changes the model. The paper admits this, and [treats it as a bandit anyway], because it's simple and it works.",
    # 3. mapping
    "mp1": "Now map it onto training. [Each arm is a category of problems]. In most experiments, that's [a difficulty level]. Pulling an arm means [putting problems from that category into the batch]. And the payout should measure [how much the model learned from them].",
    "mp2": "The real goal, [final test accuracy], is only known after training ends. So the method needs a payout it can measure [at every single step]. Its answer is [the absolute advantage].",
    # 4. advantage
    "ad1": "Math piece one: [the advantage]. In G R P O, each problem gets [eight attempts]. Say [two are correct, and six are wrong]. The mean reward is [one quarter].",
    "ad2": "The advantage of each attempt is [its reward, minus the group mean, divided by the group's standard deviation]. Here, the standard deviation is [about zero point four three].",
    "ad3": "So the two correct attempts get an advantage of [plus one point seven three]: push them up. The six wrong ones get [minus zero point five eight]: push them down. Average the absolute values, and you get [about zero point eight seven].",
    "ad4": "If [all eight attempts are correct], every reward equals the mean, and [every advantage is zero]. No push in any direction. That's the too-easy case, in numbers.",
    # 5. gradient
    "gr1": "Math piece two: why the absolute advantage measures learning. The policy gradient loss is [minus the log probability of each sampled token, multiplied by its advantage].",
    "gr2": "Take the gradient, and [the advantage comes out as a multiplier]. So the size of the update is roughly [the absolute advantage, times the size of the gradient of the log probability].",
    "gr3": "Big absolute advantage, [big update]. Zero advantage, [no update]. So the payout of a category is [the average absolute advantage over all the attempts from that category in the batch]. And it costs nothing extra, because [G R P O already computed those advantages].",
    # 6. peak at one half
    "pk1": "Math piece three, from the appendix. Suppose a problem has [success rate p]. A correct attempt happens [with probability p], and its absolute advantage is [one minus p, over the square root of p times one minus p].",
    "pk2": "A wrong attempt happens [with probability one minus p], and its absolute advantage is [p, over that same square root].",
    "pk3": "Add the two cases, weighted by their probabilities, and it simplifies to [two times the square root of p times one minus p].",
    "pk4": "[Plot it.] It's [zero when the model always fails], [zero when it always succeeds], and it peaks [exactly at a fifty percent success rate]. So chasing absolute advantage means chasing problems the model solves about half the time. Not too easy, not too hard. Educators call this [the zone of proximal development].",
    # 7. score update
    "up1": "Math piece four: keeping score. After each step, the method updates the score of [every category it sampled]. The new score is [alpha times today's payout, plus one minus alpha times the old score]. All scores [start at zero].",
    "up2": "This is the T D zero update from reinforcement learning. For a bandit, it's simply [an exponential moving average]. Unroll it, and the payout from k steps ago has a weight of [alpha, times one minus alpha to the power k]. [Recent steps count most, and old ones fade away].",
    "up3": "With alpha equal to one half, as in most of the paper's runs, a payout from five steps ago keeps [less than two percent of the weight]. That fast forgetting is exactly [what a non-stationary bandit needs].",
    # 8. softmax
    "sm1": "Math piece five: choosing arms. The method doesn't just take the best score. It turns the scores into probabilities with [a softmax, also called a Boltzmann distribution]. Each category's weight is [e to the power of its score, divided by a temperature, tau].",
    "sm2": "Take three levels with scores of [zero point three, zero point eight, and zero point five]. With tau equal to one, the probabilities are [twenty-six, forty-three, and thirty-two percent]. Still a broad mix.",
    "sm3": "Lower tau to zero point two, and they become [six, seventy-seven, and seventeen percent]. Low temperature [exploits the best arm]. High temperature [explores]. The batch is filled by sampling a category this way, then [a random problem from inside it], until the batch holds [two hundred fifty-six problems].",
    # 9. loop
    "lp1": "Put it together. One: [sample the batch from the softmax over scores]. Two: [run G R P O as usual]: attempts, rewards, advantages, and an update. Three: [average the absolute advantages per category]. Four: [update the scores]. Then [repeat].",
    "lp2": "That's the whole algorithm. A few lines on top of a normal training loop, with [two new hyperparameters, alpha and tau].",
    # 10. simulation
    "si1": "Let's watch it run on a toy model, with three difficulty levels and a model that improves as it learns. [This is a simulation for intuition, not the paper's data.] On the left is [the curve from before], and each dot is [one level, at its current success rate].",
    "si2": "At first, the easy level sits near the peak, so it pays the most and [gets sampled the most]. As the model improves, [the easy dot slides past the peak, and its payout drops, while the harder levels climb toward fifty percent. The sampling shifts toward harder problems, all on its own.]",
    "si3": "This is what the paper reports in [its third figure]. Across all tasks, the sampled difficulty [starts below the dataset's average, and moves above it] as training goes on. And it picks [harder problems for the stronger, seven billion parameter model].",
    # 11. results
    "rs1": "Now, the results. They fine-tune [Qwen two point five, at three and seven billion parameters], with G R P O, on [Countdown, Zebra puzzles, ARC one D, and math]. For the puzzles, they train on [the three easiest levels], and test out of distribution on [a harder fourth level].",
    "rs2": "For the three billion model, [the method helps most out of distribution]. Countdown goes from [zero point four eight with random sampling to zero point five four]. Zebra [from zero point two nine to zero point three five]. ARC [from zero point three one to zero point three eight]. The fixed easy-to-hard ordering is mixed: [terrible on Countdown, but better than random on Zebra and ARC].",
    "rs3": "For the seven billion model, [the gains shrink]. On Countdown and ARC out of distribution, [random is actually slightly better]. When they make Countdown harder, [the gain comes back: from zero point three seven to zero point four four].",
    "rs4": "Two more results. When they [mix three tasks, with nine arms, one for every task and difficulty pair], random training collapses midway on Countdown, while the bandit stays stable. And the method [also helps with P P O and R L O O], not just G R P O.",
    # 12. questions
    "q1": "Finally, questions to bring to the discussion. First: [is it just tracking success rate]? With binary rewards, [the payout is a fixed function of p]. So the method is close to: estimate each level's accuracy, and prefer levels near fifty percent. How much does the bandit machinery really add?",
    "q2": "Second: noise. [The AIME benchmark has thirty problems]. Going from zero point zero seven five to zero point one is [less than one extra problem solved on average], and the paper [reports no error bars].",
    "q3": "Third: tuning. [Alpha and tau are tuned per task and model], while the random baseline has nothing to tune. And fourth: [a big gradient is not the same as useful learning]. Earlier work, [teacher student curriculum learning], used measured progress instead.",
    "q4": "And for your own chess project: [puzzle rating bands are natural arms]. Your fixed curriculum stages could become [a sampler like this one], fed by [the G R P O advantages you already compute]. That's the whole paper. Enjoy the reading group.",
}
